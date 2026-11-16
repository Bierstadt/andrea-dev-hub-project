"""
main.py - DLL Developer Hub Prototype (command-line version)

This is the command-line version of the app. It implements the home menu plus
the main activities from the project spec:
  1) API Catalog         - browse/search finance API products and view their specs
  2) Request Credentials - submit (simulated) credential requests and check status
  3) Admin Review        - approve requests or ask for more information

In Version 2 all of the "logic" (loading data, searching, validating, saving,
reviewing) moved to hub_logic.py so the Streamlit app (app.py) can reuse it.
This file now only handles printing and keyboard input.

Functions marked "AI-generated" below were added with AI help because I was having a
difficult time writing them myself.
"""

import json

import hub_logic as logic


def ask_yes_no(prompt):
    """Ask a yes/no question until the user answers yes or no.

    Args:
        prompt (str): Question to show.

    Returns:
        str: "yes" or "no".
    """
    while True:
        answer = input(prompt).strip().lower()
        if answer in logic.YES_NO:
            return answer
        print("Please type yes or no.")


def choose_number(prompt, count):
    """Ask the user for a number between 1 and count.

    Args:
        prompt (str): Question to show.
        count (int): Highest allowed number.

    Returns:
        int or None: Zero-based index of the choice, or None if the user
        pressed Enter or typed something that isn't a valid number.
    """
    choice = input(prompt).strip()
    if choice.isdigit() and 1 <= int(choice) <= count:
        return int(choice) - 1
    if choice:
        print("That isn't one of the choices.")
    return None


def show_home_menu():
    """Display the home page choices and return the user's selection."""
    print("\n=== DLL Developer Hub ===")
    print("1) API Catalog")
    print("2) Request Credentials")
    print("3) Admin Review")
    print("4) Exit")
    return input("Select an option (1-4): ").strip()


def show_api_product(product):
    """Print a short overview of a single API product."""
    print(f"\n--- {product['name']} ---")
    print(product["overview"])
    print(f"Common uses: {', '.join(product['common_uses'])}")
    print(f"Basic requirements: {', '.join(product['requirements'])}")
    print(f"Environments: {', '.join(product['environments'])}")


def show_operation_list(operations):
    """Print a numbered list of API operations."""
    for i, op in enumerate(operations, start=1):
        print(f"{i}) {op['operation']} ({op['method']} {op['path']})")


def show_api_spec(operation):
    """Print one simplified API operation: method, path, required fields, samples."""
    print(f"\nOperation: {operation['operation']}")
    print(f"Method: {operation['method']}  Path: {operation['path']}")
    print(f"Required fields: {', '.join(operation['required_fields'])}")
    print("Sample request:", json.dumps(operation["sample_request"], indent=2))
    print("Sample response:", json.dumps(operation["sample_response"], indent=2))


# AI-generated: masks the credential with string slicing, showing
# the first 7 characters and replacing the rest with "*".
def show_credentials(request, reveal=False):
    """Display a credential request's status and a masked (or revealed) sample key."""
    print(f"\nRequest {request['request_id']} - Status: {request['status']}")
    print(f"API: {request['product_id']}  Environment: {request['environment']}")
    print(f"Operations: {', '.join(request.get('operations', []))}")
    if request.get("review_note"):
        print(f"Reviewer note: {request['review_note']}")
    credential = request.get("sample_credential")
    if not credential:
        print("No credential available yet.")
        return
    shown = credential if reveal else logic.mask_credential(credential)
    print(f"Sample credential: {shown}")


# AI-generated: uses a nested helper function, ask(), that returns a
# hardcoded answer if one was passed in, otherwise falls back to input().
def collect_credential_request(product_id, operations, answers=None):
    """Gather credential request details for an API product.

    Args:
        product_id (str): Product the request is for.
        operations (list): Operation names already chosen by the user.
        answers (dict, optional): Hardcoded answers, used for testing
            without typing anything.

    Returns:
        dict: The new (not yet saved) request.
    """
    if answers is None:
        answers = {}

    def ask(key, prompt):
        return answers[key] if key in answers else input(prompt).strip()

    details = {
        "environment": ask("environment", "Environment (sandbox/production): "),
        "name": ask("name", "Your name: "),
        "organization": ask("organization", "Organization: "),
        "email": ask("email", "Email address: "),
        "intended_use": ask("intended_use", "Briefly describe intended use: "),
        "reviewed_guide": ask("reviewed_guide", "Have you reviewed the API guide? (yes/no): "),
        "technical_contact": ask("technical_contact", "Is a technical contact available? (yes/no): "),
    }
    return logic.build_credential_request(product_id, operations, details)


def run_catalog_flow(catalog, api_specs):
    """Handle the API Catalog menu: search, view overview, and view spec."""
    search_text = input("Search APIs (press Enter to see all): ")
    matches = logic.search_catalog(catalog, search_text)
    if not matches:
        print("No matching API products found.")
        return

    print("\nMatching API products:")
    for i, product in enumerate(matches, start=1):
        print(f"{i}) {product['name']} - {product['goal']}")

    index = choose_number("Select a product number (or Enter to go back): ", len(matches))
    if index is None:
        return
    product = matches[index]
    show_api_product(product)

    operations = logic.get_operations(product["id"], api_specs)
    if not operations:
        print("No API specification available for this product yet.")
        return
    if ask_yes_no("View API specification? (yes/no): ") != "yes":
        return

    print("\nOperations:")
    show_operation_list(operations)
    pick = choose_number("Select an operation number: ", len(operations))
    if pick is not None:
        show_api_spec(operations[pick])


def run_resubmit_flow(request, requests_list):
    """Let the requester answer a Needs Information note and resubmit."""
    print("\nUpdate your answers (press Enter to keep the current one).")
    intended_use = input(f"Intended use [{request['intended_use']}]: ").strip() or request["intended_use"]
    updates = {
        "intended_use": intended_use,
        "reviewed_guide": ask_yes_no("Have you reviewed the API guide? (yes/no): "),
        "technical_contact": ask_yes_no("Is a technical contact available? (yes/no): "),
    }
    response = input("Message to the reviewer (optional): ")
    try:
        logic.resubmit_request(request, requests_list, updates, response)
        print("Request resubmitted for review.")
    except ValueError as err:
        print(err)


def run_status_lookup(requests_list):
    """Ask for a request ID, show its status, and offer to reveal the key or resubmit."""
    request = logic.find_request(input("Enter your request ID: "), requests_list)
    if not request:
        print("Request not found. Check the ID (it looks like REQ-AB12CD).")
        return
    show_credentials(request)
    if request.get("sample_credential") and ask_yes_no("Reveal full key? (yes/no): ") == "yes":
        show_credentials(request, reveal=True)
    if request["status"] == logic.STATUS_NEEDS_INFO and \
            ask_yes_no("Update and resubmit this request? (yes/no): ") == "yes":
        run_resubmit_flow(request, requests_list)


# AI-generated: branches between new/existing requests and chains
# collect -> validate -> save -> show.
def run_credential_flow(catalog, api_specs, requests_list):
    """Handle the Request Credentials menu: start a new request or check an existing one."""
    choice = input("1) New request  2) View existing request: ").strip()
    if choice == "2":
        run_status_lookup(requests_list)
        return
    if choice != "1":
        print("Please choose 1 or 2.")
        return

    print("\nAvailable APIs:")
    for product in catalog:
        print(f"- {product['id']}: {product['name']}")
    product_id = input("Enter the API id to request credentials for: ").strip().lower()
    if not logic.find_product(product_id, catalog):
        print(f"'{product_id}' is not an API in the catalog.")
        return

    print("\nOperations:")
    operations = logic.get_operations(product_id, api_specs)
    show_operation_list(operations)
    chosen = logic.parse_operation_selection(input("Select operations (e.g. 1,2): "), operations)
    request = collect_credential_request(product_id, chosen)

    problems = logic.validate_request(request, catalog)
    if problems:
        print("\nPlease fix the following and try again:")
        for problem in problems:
            print(f"- {problem}")
        return

    saved = logic.save_request(request, requests_list)
    print(f"\nRequest submitted! Your request ID is {saved['request_id']}.")
    print("An admin will review it. Use 'View existing request' with this ID to check its status.")
    show_credentials(saved)


def run_admin_flow(requests_list):
    """Handle the Admin Review menu: approve or send back Submitted requests."""
    waiting = logic.list_requests_by_status(requests_list, logic.STATUS_SUBMITTED)
    if not waiting:
        print("\nNo requests are waiting for review.")
        return

    print("\nRequests waiting for review:")
    for i, request in enumerate(waiting, start=1):
        print(f"{i}) {request['request_id']} - {request['name']} ({request['organization']}) "
              f"- {request['product_id']} / {request['environment']}")
    index = choose_number("Select a request to review (or Enter to go back): ", len(waiting))
    if index is None:
        return
    request = waiting[index]
    if request.get("previous_review_note"):
        print(f"You previously asked: {request['previous_review_note']}")
    if request.get("requester_response"):
        print(f"Requester's response: {request['requester_response']}")
    print(f"Intended use: {request['intended_use']}")
    print(f"Reviewed guide: {request['reviewed_guide']}  Technical contact: {request['technical_contact']}")

    action = input("1) Approve  2) Needs more information: ").strip()
    if action == "1":
        logic.approve_request(request, requests_list)
        print("Approved. A sample credential was issued.")
    elif action == "2":
        suggestion = logic.suggest_review_note(request)
        prompt = f"Note to requester [{suggestion}]: " if suggestion else "Note to requester: "
        note = input(prompt).strip() or suggestion
        try:
            logic.request_more_info(request, requests_list, note)
            print("Request marked Needs Information.")
        except ValueError as err:
            print(err)
    else:
        print("No changes made.")


def main():
    """Control the overall program loop: load data, show home menu, dispatch flows."""
    try:
        catalog, api_specs, requests_list = logic.load_hub_data()
    except logic.DataFileError as err:
        print(f"Sorry, the app could not start: {err}")
        return

    while True:
        choice = show_home_menu()
        try:
            if choice == "1":
                run_catalog_flow(catalog, api_specs)
            elif choice == "2":
                run_credential_flow(catalog, api_specs, requests_list)
            elif choice == "3":
                run_admin_flow(requests_list)
            elif choice == "4":
                print("Goodbye!")
                break
            else:
                print("Please choose 1, 2, 3, or 4.")
        except logic.DataFileError as err:
            print(f"Something went wrong saving your data: {err}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
