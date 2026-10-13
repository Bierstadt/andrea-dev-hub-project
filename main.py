"""
main.py - DLL Developer Hub Prototype (Version 1, CLI)

This is the file run by the end user. It implements the home menu plus the
two main activities from the project spec:
  1) API Catalog   - browse/search finance API products and view their specs
  2) Request Credentials - submit (simulated) credential requests and check status

Data is loaded from local JSON files in the data/ folder. Most functions
below accept an optional "hardcoded" argument so they can be tested without
typing anything at the keyboard (see the spec's "block" testing approach).

Functions marked "AI-generated" below were added with AI help because I was having a
difficult time writing them myself.
"""

import json
import os
import random
import string

DATA_DIR = "data"
CATALOG_FILE = os.path.join(DATA_DIR, "catalog.json")
API_SPECS_FILE = os.path.join(DATA_DIR, "api_specs.json")
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.json")


def load_data():
    """Load catalog, API spec, and saved request data from local JSON files."""
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    with open(API_SPECS_FILE, "r", encoding="utf-8") as f:
        api_specs = json.load(f)
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
            requests_list = json.load(f)
    else:
        requests_list = []
    return catalog, api_specs, requests_list


def show_home_menu():
    """Display the two main home page choices and return the user's selection."""
    print("\n=== DLL Developer Hub ===")
    print("1) API Catalog")
    print("2) Request Credentials")
    print("3) Exit")
    return input("Select an option (1-3): ").strip()


def find_product(product_id, catalog):
    """Return the catalog product with this id, or None if it doesn't exist."""
    for product in catalog:
        if product["id"] == product_id:
            return product
    return None


# AI-generated: builds one combined search string per product and
# does a case-insensitive substring match against it.
def search_catalog(catalog, search_text=""):
    """Return the API products whose name, overview, or keywords match search_text."""
    if not search_text:
        return catalog
    text = search_text.lower()
    matches = []
    for product in catalog:
        haystack = " ".join([
            product.get("name", ""),
            product.get("overview", ""),
            " ".join(product.get("keywords", [])),
        ]).lower()
        if text in haystack:
            matches.append(product)
    return matches


def show_api_product(product):
    """Print a short overview of a single API product."""
    print(f"\n--- {product['name']} ---")
    print(product["overview"])
    print(f"Common uses: {', '.join(product['common_uses'])}")
    print(f"Basic requirements: {', '.join(product['requirements'])}")
    print(f"Environments: {', '.join(product['environments'])}")


def show_api_spec(product_id, api_specs, operation_index=0):
    """Print one simplified API operation: method, path, required fields, samples."""
    operations = api_specs.get(product_id, [])
    if not operations:
        print("No API specification available for this product yet.")
        return
    if operation_index < 0 or operation_index >= len(operations):
        operation_index = 0
    op = operations[operation_index]
    print(f"\nOperation: {op['operation']}")
    print(f"Method: {op['method']}  Path: {op['path']}")
    print(f"Required fields: {', '.join(op['required_fields'])}")
    print("Sample request:", json.dumps(op["sample_request"], indent=2))
    print("Sample response:", json.dumps(op["sample_response"], indent=2))


def list_operations(product_id, api_specs):
    """Print a numbered list of the operations available for an API product."""
    operations = api_specs.get(product_id, [])
    for i, op in enumerate(operations, start=1):
        print(f"{i}) {op['operation']} ({op['method']} {op['path']})")
    return operations


# Parses a comma-separated list like "1,2" into
# operation names, skipping anything that isn't a valid number.
def choose_operations(product_id, api_specs, selection=None):
    """
    Let the user pick one or more operations by number (e.g. "1,2").
    Pass `selection` to supply a hardcoded answer for testing.
    Returns a list of operation names (empty if nothing valid was chosen).
    """
    operations = list_operations(product_id, api_specs)
    if selection is None:
        selection = input("Select operations (e.g. 1,2): ").strip()
    chosen = []
    for part in selection.split(","):
        part = part.strip()
        if part.isdigit() and 1 <= int(part) <= len(operations):
            name = operations[int(part) - 1]["operation"]
            if name not in chosen:
                chosen.append(name)
    return chosen


# AI-generated: uses a nested helper function, ask(), that returns a
# hardcoded answer if one was passed in, otherwise falls back to input().
def collect_credential_request(product_id, answers=None):
    """
    Gather credential request details for a given API product.
    Pass `answers` (a dict) to supply hardcoded values instead of using input() -
    this is how the function can be tested without typing anything.
    """
    if answers is None:
        answers = {}

    def ask(key, prompt):
        return answers[key] if key in answers else input(prompt).strip()

    request = {
        "product_id": product_id,
        "environment": ask("environment", "Environment (sandbox/production): "),
        "name": ask("name", "Your name: "),
        "organization": ask("organization", "Organization: "),
        "email": ask("email", "Email address: "),
        "intended_use": ask("intended_use", "Briefly describe intended use: "),
        "reviewed_guide": ask("reviewed_guide", "Have you reviewed the API guide? (yes/no): "),
        "technical_contact": ask("technical_contact", "Is a technical contact available? (yes/no): "),
    }
    return request


def validate_request(request):
    """Return a list of missing or invalid fields for a credential request."""
    required_fields = [
        "environment", "name", "organization", "email",
        "intended_use", "reviewed_guide", "technical_contact",
    ]
    missing = [field for field in required_fields if not request.get(field)]
    if not request.get("operations"):
        missing.append("operations (choose at least one)")
    if request.get("environment", "").lower() not in ("sandbox", "production"):
        missing.append("environment (must be sandbox/production)")
    if "@" not in request.get("email", ""):
        missing.append("email (must contain @)")
    if request.get("reviewed_guide", "").lower() not in ("yes", "no"):
        missing.append("reviewed_guide (must be yes/no)")
    if request.get("technical_contact", "").lower() not in ("yes", "no"):
        missing.append("technical_contact (must be yes/no)")
    return missing


def _generate_request_id():
    """Create a short, readable request ID, e.g. REQ-7F3K9A."""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"REQ-{suffix}"


def write_requests(requests_list):
    """Save the full list of requests to data/requests.json."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(requests_list, f, indent=2)


# AI-generated: generates a random request ID and saves the request
# with status "Submitted" (no credential yet).
def save_request(request, requests_list):
    """Assign a request ID, mark it Submitted, append to requests_list, and persist."""
    request["request_id"] = _generate_request_id()
    request["status"] = "Submitted"
    requests_list.append(request)
    write_requests(requests_list)
    return request


# Simulated review step. Requests where the user hasn't
# reviewed the guide or has no technical contact go to "Needs Information";
# everything else gets a sample key and "Credentials Available".
def review_request(request, requests_list):
    """Simulate the review of a Submitted request and update its status."""
    if request["status"] != "Submitted":
        return request
    if request["reviewed_guide"].lower() != "yes" or request["technical_contact"].lower() != "yes":
        request["status"] = "Needs Information"
        request["review_note"] = "Please review the API guide and provide a technical contact."
    else:
        request["status"] = "Credentials Available"
        request["sample_credential"] = "sk_test_" + "".join(
            random.choices(string.ascii_lowercase + string.digits, k=20)
        )
    write_requests(requests_list)
    return request


def find_request(request_id, requests_list):
    """Look up a saved request by its request ID. Returns None if not found."""
    for request in requests_list:
        if request.get("request_id") == request_id:
            return request
    return None


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
    if reveal:
        print(f"Sample credential: {credential}")
    else:
        print(f"Sample credential: {credential[:7]}{'*' * (len(credential) - 7)}")


def run_catalog_flow(catalog, api_specs):
    """Handle the API Catalog menu: search, view overview, and view spec."""
    search_text = input("Search APIs (press Enter to see all): ").strip()
    matches = search_catalog(catalog, search_text)
    if not matches:
        print("No matching API products found.")
        return

    print("\nMatching API products:")
    for i, product in enumerate(matches, start=1):
        print(f"{i}) {product['name']} - {product['goal']}")

    choice = input("Select a product number (or Enter to go back): ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(matches)):
        return

    product = matches[int(choice) - 1]
    show_api_product(product)

    if input("View API specification? (yes/no): ").strip().lower() != "yes":
        return

    print("\nOperations:")
    operations = list_operations(product["id"], api_specs)
    pick = input("Select an operation number: ").strip()
    if pick.isdigit() and 1 <= int(pick) <= len(operations):
        show_api_spec(product["id"], api_specs, int(pick) - 1)
    else:
        print("Invalid choice.")


# AI-generated: branches between new/existing requests and chains
# collect -> validate -> save -> show. Existing "Submitted" requests
# can be sent through the simulated review step.
def run_credential_flow(catalog, api_specs, requests_list):
    """Handle the Request Credentials menu: start a new request or check an existing one."""
    choice = input("1) New request  2) View existing request: ").strip()

    if choice == "2":
        request_id = input("Enter your request ID: ").strip().upper()
        request = find_request(request_id, requests_list)
        if not request:
            print("Request not found.")
            return
        show_credentials(request)
        if request["status"] == "Submitted":
            if input("Simulate review now? (yes/no): ").strip().lower() == "yes":
                review_request(request, requests_list)
                show_credentials(request)
        return

    print("\nAvailable APIs:")
    for product in catalog:
        print(f"- {product['id']}: {product['name']}")
    product_id = input("Enter the API id to request credentials for: ").strip().lower()
    if not find_product(product_id, catalog):
        print(f"'{product_id}' is not an API in the catalog.")
        return

    print("\nOperations:")
    operations = choose_operations(product_id, api_specs)
    request = collect_credential_request(product_id)
    request["operations"] = operations
    missing = validate_request(request)
    if missing:
        print("\nMissing or invalid information:")
        for field in missing:
            print(f"- {field}")
        return

    saved = save_request(request, requests_list)
    print(f"\nRequest submitted! Your request ID is {saved['request_id']}.")
    print("Use 'View existing request' with this ID to check its status.")
    show_credentials(saved)


def main():
    """Control the overall program loop: load data, show home menu, dispatch flows."""
    catalog, api_specs, requests_list = load_data()

    while True:
        choice = show_home_menu()
        if choice == "1":
            run_catalog_flow(catalog, api_specs)
        elif choice == "2":
            run_credential_flow(catalog, api_specs, requests_list)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Please choose 1, 2, or 3.")


if __name__ == "__main__":
    main()
