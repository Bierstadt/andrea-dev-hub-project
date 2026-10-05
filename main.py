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
    if request.get("reviewed_guide", "").lower() not in ("yes", "no"):
        missing.append("reviewed_guide (must be yes/no)")
    if request.get("technical_contact", "").lower() not in ("yes", "no"):
        missing.append("technical_contact (must be yes/no)")
    return missing


def _generate_request_id():
    """Create a short, readable request ID, e.g. REQ-7F3K9A."""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"REQ-{suffix}"


# AI-generated: generates a random request ID and sample key,
# simulates approval, and rewrites requests.json.
# TODO: save as "Submitted" first and approve in a separate step.
def save_request(request, requests_list):
    """
    Assign a request ID/status, simulate an approval step (per the class
    prototype scope), append to requests_list, and persist to JSON.
    """
    request["request_id"] = _generate_request_id()

    # Simulated review step - real projects would wait for a human/process here.
    request["status"] = "Approved"
    request["sample_credential"] = "sk_test_" + "".join(
        random.choices(string.ascii_lowercase + string.digits, k=20)
    )

    requests_list.append(request)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(requests_list, f, indent=2)
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

    if input("View API specification? (yes/no): ").strip().lower() == "yes":
        show_api_spec(product["id"], api_specs)


# AI-generated: branches between new/existing requests and chains
# collect -> validate -> save -> show.
# TODO: reject API ids that aren't in the catalog.
def run_credential_flow(catalog, requests_list):
    """Handle the Request Credentials menu: start a new request or check an existing one."""
    choice = input("1) New request  2) View existing request: ").strip()

    if choice == "2":
        request_id = input("Enter your request ID: ").strip()
        request = find_request(request_id, requests_list)
        if request:
            show_credentials(request)
        else:
            print("Request not found.")
        return

    print("\nAvailable APIs:")
    for product in catalog:
        print(f"- {product['id']}: {product['name']}")
    product_id = input("Enter the API id to request credentials for: ").strip()

    request = collect_credential_request(product_id)
    missing = validate_request(request)
    if missing:
        print("\nMissing or invalid information:")
        for field in missing:
            print(f"- {field}")
        return

    saved = save_request(request, requests_list)
    print(f"\nRequest submitted! Your request ID is {saved['request_id']}.")
    show_credentials(saved)


def main():
    """Control the overall program loop: load data, show home menu, dispatch flows."""
    catalog, api_specs, requests_list = load_data()

    while True:
        choice = show_home_menu()
        if choice == "1":
            run_catalog_flow(catalog, api_specs)
        elif choice == "2":
            run_credential_flow(catalog, requests_list)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Please choose 1, 2, or 3.")


if __name__ == "__main__":
    main()
