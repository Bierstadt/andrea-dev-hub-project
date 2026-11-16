"""
hub_logic.py - DLL Developer Hub "logic" functions (Version 2)

These functions do the actual work of the app (load data, search, validate,
save, review) but never call print() or input(). That way both the command
line version (main.py) and the Streamlit version (app.py) can reuse them.

Written with AI assistance (GitHub Copilot) while refactoring Version 1.
"""

import json
import os
import random
import string

# Build paths from this file's location so the app works no matter which
# folder the terminal is in when it is started.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CATALOG_FILE = os.path.join(DATA_DIR, "catalog.json")
API_SPECS_FILE = os.path.join(DATA_DIR, "api_specs.json")
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.json")

ENVIRONMENTS = ("sandbox", "production")
YES_NO = ("yes", "no")

STATUS_SUBMITTED = "Submitted"
STATUS_AVAILABLE = "Credentials Available"
STATUS_NEEDS_INFO = "Needs Information"

REQUIRED_FIELDS = (
    "environment", "name", "organization", "email",
    "intended_use", "reviewed_guide", "technical_contact",
)

# Fields a requester may change when answering a "Needs Information" note.
RESUBMIT_FIELDS = ("intended_use", "reviewed_guide", "technical_contact")


class DataFileError(Exception):
    """Raised when a data file is missing, unreadable, or not valid JSON."""


def read_json_file(path, default=None):
    """Read and parse a JSON file.

    Args:
        path (str): Full path to the JSON file.
        default: Value to return if the file does not exist. If None, a
            missing file is treated as an error.

    Returns:
        The parsed JSON data (usually a list or dict).

    Raises:
        DataFileError: If the file is missing (and no default was given),
            cannot be read, or does not contain valid JSON.
    """
    if not os.path.exists(path):
        if default is not None:
            return default
        raise DataFileError(f"Data file not found: {os.path.basename(path)}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as err:
        raise DataFileError(
            f"{os.path.basename(path)} is not valid JSON (line {err.lineno})."
        ) from err
    except OSError as err:
        raise DataFileError(f"Could not read {os.path.basename(path)}: {err}") from err


def load_hub_data():
    """Load the catalog, API specs, and saved requests from the data/ folder.

    Returns:
        tuple: (catalog, api_specs, requests_list) where catalog is a list of
        product dicts, api_specs is a dict of product id -> list of operations,
        and requests_list is a list of saved request dicts.

    Raises:
        DataFileError: If the catalog or API spec file is missing or invalid.
    """
    catalog = read_json_file(CATALOG_FILE)
    api_specs = read_json_file(API_SPECS_FILE)
    requests_list = read_json_file(REQUESTS_FILE, default=[])
    assert isinstance(catalog, list), "catalog.json should contain a list of products"
    assert isinstance(api_specs, dict), "api_specs.json should contain a dict"
    assert isinstance(requests_list, list), "requests.json should contain a list"
    return catalog, api_specs, requests_list


def find_product(product_id, catalog):
    """Find a catalog product by its id.

    Args:
        product_id (str): Product id such as "quote".
        catalog (list): List of product dicts.

    Returns:
        dict or None: The matching product, or None if it doesn't exist.
    """
    for product in catalog:
        if product["id"] == product_id:
            return product
    return None


def get_product_name(product_id, catalog):
    """Get a product's display name, falling back to its id if it is unknown.

    Args:
        product_id (str): Product id such as "quote".
        catalog (list): List of product dicts.

    Returns:
        str: The product name, e.g. "Quote API".
    """
    product = find_product(product_id, catalog)
    return product["name"] if product else product_id


# AI-generated: builds one combined search string per product and
# does a case-insensitive substring match against it.
def search_catalog(catalog, search_text=""):
    """Find the API products whose name, overview, or keywords match the text.

    Args:
        catalog (list): List of product dicts.
        search_text (str): Text to search for. Empty text returns everything.

    Returns:
        list: Matching product dicts (in catalog order).
    """
    text = (search_text or "").strip().lower()
    if not text:
        return catalog
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


def get_operations(product_id, api_specs):
    """Get the list of API operations for a product.

    Args:
        product_id (str): Product id such as "quote".
        api_specs (dict): Product id -> list of operation dicts.

    Returns:
        list: Operation dicts (empty list if the product has no spec).
    """
    return api_specs.get(product_id, [])


def get_operation_names(product_id, api_specs):
    """Get just the operation names for a product (used for pick lists)."""
    return [op["operation"] for op in get_operations(product_id, api_specs)]


def parse_operation_selection(selection, operations):
    """Turn a comma-separated list of numbers (e.g. "1,2") into operation names.

    Invalid numbers and duplicates are skipped.

    Args:
        selection (str): What the user typed, e.g. "1, 2".
        operations (list): Operation dicts in the order they were shown.

    Returns:
        list: Chosen operation names (empty if nothing valid was chosen).
    """
    chosen = []
    for part in (selection or "").split(","):
        part = part.strip()
        if part.isdigit() and 1 <= int(part) <= len(operations):
            name = operations[int(part) - 1]["operation"]
            if name not in chosen:
                chosen.append(name)
    return chosen


def build_credential_request(product_id, operations, details):
    """Create a new credential request dict from the user's answers.

    Text answers are stripped, and environment / yes-no answers are
    lower-cased so later checks don't depend on capitalization.

    Args:
        product_id (str): Product the request is for.
        operations (list): Operation names the user wants access to.
        details (dict): The form answers (environment, name, organization,
            email, intended_use, reviewed_guide, technical_contact).

    Returns:
        dict: The new (not yet saved) request.
    """
    request = {"product_id": product_id, "operations": list(operations)}
    for field in REQUIRED_FIELDS:
        request[field] = str(details.get(field, "")).strip()
    for field in ("environment", "reviewed_guide", "technical_contact"):
        request[field] = request[field].lower()
    return request


def validate_request(request, catalog=None):
    """Check a credential request for missing or invalid information.

    Args:
        request (dict): The request to check.
        catalog (list, optional): If given, also check the product id exists.

    Returns:
        list: Human-readable problems. An empty list means the request is OK.
    """
    problems = [f"{field} is required" for field in REQUIRED_FIELDS if not request.get(field)]
    if catalog is not None and not find_product(request.get("product_id"), catalog):
        problems.append("API product is not in the catalog")
    if not request.get("operations"):
        problems.append("choose at least one operation")
    if request.get("environment") and request["environment"].lower() not in ENVIRONMENTS:
        problems.append("environment must be sandbox or production")
    email = request.get("email", "")
    if email and ("@" not in email or "." not in email.split("@")[-1]):
        problems.append("email must look like name@company.com")
    for field in ("reviewed_guide", "technical_contact"):
        if request.get(field) and request[field].lower() not in YES_NO:
            problems.append(f"{field} must be yes or no")
    return problems


def generate_request_id(existing_requests=()):
    """Create a short, readable, unique request ID such as REQ-7F3K9A.

    Args:
        existing_requests (list): Saved requests, used to avoid duplicate IDs.

    Returns:
        str: A new request ID.
    """
    used = {r.get("request_id") for r in existing_requests}
    while True:
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        request_id = f"REQ-{suffix}"
        if request_id not in used:
            return request_id


def generate_sample_credential():
    """Create a fake sample API key (never a real secret)."""
    return "sk_test_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=20))


def write_requests(requests_list):
    """Save the full list of requests to data/requests.json.

    Raises:
        DataFileError: If the file cannot be written.
    """
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump(requests_list, f, indent=2)
    except OSError as err:
        raise DataFileError(f"Could not save requests: {err}") from err


# AI-generated: generates a random request ID and saves the request
# with status "Submitted" (no credential yet).
def save_request(request, requests_list):
    """Give a request an ID, mark it Submitted, add it to the list, and save.

    Args:
        request (dict): A request that has already passed validate_request().
        requests_list (list): All saved requests (changed in place).

    Returns:
        dict: The saved request, now including request_id and status.
    """
    assert not validate_request(request), "save_request() needs a valid request"
    request["request_id"] = generate_request_id(requests_list)
    request["status"] = STATUS_SUBMITTED
    requests_list.append(request)
    write_requests(requests_list)
    return request


def find_request(request_id, requests_list):
    """Look up a saved request by ID (not case sensitive).

    Args:
        request_id (str): ID typed by the user, e.g. "req-7f3k9a".
        requests_list (list): All saved requests.

    Returns:
        dict or None: The matching request, or None if not found.
    """
    wanted = (request_id or "").strip().upper()
    for request in requests_list:
        if request.get("request_id") == wanted:
            return request
    return None


def list_requests_by_status(requests_list, status):
    """Return all requests that currently have the given status."""
    return [r for r in requests_list if r.get("status") == status]


def suggest_review_note(request):
    """Suggest an admin note based on which readiness answers were "no".

    Args:
        request (dict): A submitted request.

    Returns:
        str: A note asking only for what is actually missing (or "" if
        both readiness answers were "yes").
    """
    asks = []
    if request.get("reviewed_guide", "").lower() != "yes":
        asks.append("review the API guide")
    if request.get("technical_contact", "").lower() != "yes":
        asks.append("provide a technical contact")
    if not asks:
        return ""
    return "Please " + " and ".join(asks) + ", then resubmit."


def approve_request(request, requests_list):
    """Admin action: approve a Submitted request and attach a sample key.

    Args:
        request (dict): The request being reviewed.
        requests_list (list): All saved requests (saved after the change).

    Returns:
        dict: The updated request.

    Raises:
        ValueError: If the request is not in the Submitted status.
    """
    if request.get("status") != STATUS_SUBMITTED:
        raise ValueError(f"Only {STATUS_SUBMITTED} requests can be approved.")
    request["status"] = STATUS_AVAILABLE
    request["sample_credential"] = generate_sample_credential()
    request.pop("review_note", None)
    write_requests(requests_list)
    return request


def request_more_info(request, requests_list, note):
    """Admin action: send a Submitted request back as Needs Information.

    Args:
        request (dict): The request being reviewed.
        requests_list (list): All saved requests (saved after the change).
        note (str): Message telling the requester what is missing.

    Returns:
        dict: The updated request.

    Raises:
        ValueError: If the request is not Submitted or the note is empty.
    """
    if request.get("status") != STATUS_SUBMITTED:
        raise ValueError(f"Only {STATUS_SUBMITTED} requests can be reviewed.")
    note = (note or "").strip()
    if not note:
        raise ValueError("Please write a note explaining what information is needed.")
    request["status"] = STATUS_NEEDS_INFO
    request["review_note"] = note
    write_requests(requests_list)
    return request


def resubmit_request(request, requests_list, updates, response=""):
    """Requester action: update a Needs Information request and send it back for review.

    Only the fields in RESUBMIT_FIELDS can be changed. The reviewer's note is
    kept as "previous_review_note" so the admin can see what was asked for.

    Args:
        request (dict): The request being resubmitted.
        requests_list (list): All saved requests (saved after the change).
        updates (dict): New values for any of the RESUBMIT_FIELDS.
        response (str): Optional message from the requester to the reviewer.

    Returns:
        dict: The updated request, now back in the Submitted status.

    Raises:
        ValueError: If the request is not Needs Information or the updated
            answers are not valid.
    """
    if request.get("status") != STATUS_NEEDS_INFO:
        raise ValueError(f"Only {STATUS_NEEDS_INFO} requests can be resubmitted.")
    updated = dict(request)
    for field in RESUBMIT_FIELDS:
        if field in updates:
            updated[field] = str(updates[field]).strip()
    for field in ("reviewed_guide", "technical_contact"):
        updated[field] = updated[field].lower()
    problems = validate_request(updated)
    if problems:
        raise ValueError("Please fix the following: " + "; ".join(problems))
    response = (response or "").strip()
    unchanged = all(updated[field] == request.get(field) for field in RESUBMIT_FIELDS)
    if unchanged and not response:
        raise ValueError("Please update an answer or add a message to the reviewer before resubmitting.")

    for field in RESUBMIT_FIELDS:
        request[field] = updated[field]
    request["previous_review_note"] = request.pop("review_note", "")
    if response:
        request["requester_response"] = response
    else:
        request.pop("requester_response", None)
    request["resubmission_count"] = request.get("resubmission_count", 0) + 1
    request["status"] = STATUS_SUBMITTED
    write_requests(requests_list)
    return request


def mask_credential(credential, visible=7):
    """Hide most of a credential, e.g. "sk_test_abc123" -> "sk_test*******".

    Args:
        credential (str): The full sample key.
        visible (int): How many leading characters to keep.

    Returns:
        str: The masked key.
    """
    if not credential:
        return ""
    return credential[:visible] + "*" * max(0, len(credential) - visible)
