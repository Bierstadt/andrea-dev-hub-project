"""
app.py - DLL Developer Hub Prototype (Version 2, Streamlit)

Run with:  streamlit run app.py

Pages (built with st.navigation, so no pages/ folder is needed):
  Home, API Catalog, Request Credentials, Check Request Status, Admin Review

All the real work is done by functions in hub_logic.py; this file only
builds the web pages.

Written with AI assistance (GitHub Copilot).
"""

import streamlit as st

import hub_logic as logic

st.set_page_config(page_title="DLL Developer Hub", page_icon="🏦", layout="wide")


@st.cache_data
def load_catalog_and_specs():
    """Load the catalog and API specs once (they don't change while the app runs)."""
    catalog, api_specs, _ = logic.load_hub_data()
    return catalog, api_specs


def load_requests():
    """Read the saved requests fresh from disk so every page sees the latest data."""
    return logic.read_json_file(logic.REQUESTS_FILE, default=[])


def show_data_error(err):
    """Show a friendly error and stop the page when a data file is broken."""
    st.error(f"Sorry, the app could not load its data: {err}")
    st.stop()


def show_status_progress(status):
    """Show a simple 3-step tracker: Submitted -> Admin review -> Credentials."""
    if status == logic.STATUS_AVAILABLE:
        icons = ["✅", "✅", "✅"]
    elif status == logic.STATUS_NEEDS_INFO:
        icons = ["✅", "⚠️", "⬜"]
    else:
        icons = ["✅", "⏳", "⬜"]
    review_label = "Admin review (action needed)" if status == logic.STATUS_NEEDS_INFO else "Admin review"
    steps = ["Submitted", review_label, "Credentials available"]
    for col, icon, step in zip(st.columns(len(steps)), icons, steps):
        col.markdown(f"{icon} {step}")


def show_request_summary(request, catalog, reveal=False):
    """Show a request's status, details, reviewer note, and (masked) key."""
    status = request["status"]
    if status == logic.STATUS_AVAILABLE:
        st.success(f"Status: {status}")
    elif status == logic.STATUS_NEEDS_INFO:
        st.warning(f"Status: {status}")
    else:
        st.info(f"Status: {status} (waiting for admin review)")
    show_status_progress(status)
    st.write(f"**API:** {logic.get_product_name(request['product_id'], catalog)}  |  "
             f"**Environment:** {request['environment']}")
    st.write(f"**Operations:** {', '.join(request.get('operations', []))}")
    if request.get("review_note"):
        st.write(f"**Reviewer note:** {request['review_note']}")
    credential = request.get("sample_credential")
    if credential:
        shown = credential if reveal else logic.mask_credential(credential)
        st.code(shown, language=None)


def show_home_page():
    """Home page: short intro and links to the main activities."""
    st.title("DLL Developer Hub")
    st.write("Explore DLL finance APIs and request sandbox or production credentials.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("📚 API Catalog")
        st.write("Search API products and view simplified specifications.")
        st.page_link(CATALOG_PAGE, label="Browse APIs", icon="➡️")
    with col2:
        st.subheader("🔑 Request Credentials")
        st.write("Submit a request, then check its status with your request ID.")
        st.page_link(REQUEST_PAGE, label="New request", icon="➡️")
        st.page_link(STATUS_PAGE, label="Check status", icon="➡️")
    with col3:
        st.subheader("🛡️ Admin Review")
        st.write("Simulated reviewer: approve requests or ask for more information.")
        st.page_link(ADMIN_PAGE, label="Review requests", icon="➡️")


def show_catalog_page():
    """API Catalog page: search, pick a product, and view overview/spec tabs."""
    st.title("API Catalog")
    try:
        catalog, api_specs = load_catalog_and_specs()
    except logic.DataFileError as err:
        show_data_error(err)

    search_text = st.text_input("Search APIs", placeholder="e.g. quote, contract, payment")
    matches = logic.search_catalog(catalog, search_text)
    if not matches:
        st.info("No matching API products found. Try a different word.")
        return

    names = [p["name"] for p in matches]
    choice = st.radio("Matching API products", names, horizontal=True)
    product = matches[names.index(choice)]
    st.caption(product["goal"])

    overview_tab, spec_tab = st.tabs(["Overview", "API Specification"])
    with overview_tab:
        st.write(product["overview"])
        st.write("**Common uses:** " + ", ".join(product["common_uses"]))
        st.write("**Basic requirements:** " + ", ".join(product["requirements"]))
        st.write("**Environments:** " + ", ".join(product["environments"]))
    with spec_tab:
        operations = logic.get_operations(product["id"], api_specs)
        if not operations:
            st.info("No API specification available for this product yet.")
        else:
            labels = [f"{op['operation']} ({op['method']} {op['path']})" for op in operations]
            op = operations[labels.index(st.selectbox("Operation", labels))]
            st.write(f"**Method:** `{op['method']}`  **Path:** `{op['path']}`")
            st.write("**Required fields:** " + ", ".join(op["required_fields"]))
            left, right = st.columns(2)
            left.write("Sample request")
            left.json(op["sample_request"])
            right.write("Sample response")
            right.json(op["sample_response"])

    if st.button(f"Request credentials for {product['name']}", type="primary"):
        st.session_state["preselected_product"] = product["id"]
        st.switch_page(REQUEST_PAGE)


def show_request_page():
    """Request Credentials page: a validated form that saves a new request."""
    st.title("Request Credentials")
    try:
        catalog, api_specs = load_catalog_and_specs()
    except logic.DataFileError as err:
        show_data_error(err)

    ids = [p["id"] for p in catalog]
    preselected = st.session_state.pop("preselected_product", None)
    default_index = ids.index(preselected) if preselected in ids else 0
    # The product picker is outside the form so the operation list updates right away.
    product_id = st.selectbox(
        "API product", ids, index=default_index,
        format_func=lambda pid: logic.find_product(pid, catalog)["name"],
    )

    with st.form("credential_request", clear_on_submit=False):
        operations = st.multiselect("Operations", logic.get_operation_names(product_id, api_specs))
        environment = st.radio("Environment", logic.ENVIRONMENTS, horizontal=True)
        name = st.text_input("Your name")
        organization = st.text_input("Organization")
        email = st.text_input("Email address", placeholder="name@company.com")
        intended_use = st.text_area("Briefly describe intended use")
        reviewed_guide = st.radio("Have you reviewed the API guide?", logic.YES_NO, horizontal=True)
        technical_contact = st.radio("Is a technical contact available?", logic.YES_NO, horizontal=True)
        submitted = st.form_submit_button("Submit request", type="primary")

    if not submitted:
        return

    request = logic.build_credential_request(product_id, operations, {
        "environment": environment, "name": name, "organization": organization,
        "email": email, "intended_use": intended_use,
        "reviewed_guide": reviewed_guide, "technical_contact": technical_contact,
    })
    problems = logic.validate_request(request, catalog)
    if problems:
        st.error("Please fix the following:\n\n" + "\n".join(f"- {p}" for p in problems))
        return

    try:
        saved = logic.save_request(request, load_requests())
    except logic.DataFileError as err:
        st.error(f"Your request could not be saved: {err}")
        return
    st.success(f"Request submitted! Your request ID is **{saved['request_id']}**. "
               "Save it to check your status later.")
    st.code(saved["request_id"], language=None)
    st.session_state["last_request_id"] = saved["request_id"]
    st.page_link(STATUS_PAGE, label="Check request status", icon="➡️")


def show_resubmit_form(request, requests_list):
    """Let the requester answer a Needs Information note and resubmit."""
    st.subheader("Update and resubmit")
    st.write("Answer the reviewer's note below, then resubmit for another review.")
    rid = request["request_id"]
    with st.form(f"resubmit_{rid}"):
        intended_use = st.text_area("Briefly describe intended use", value=request["intended_use"])
        reviewed_guide = st.radio(
            "Have you reviewed the API guide?", logic.YES_NO, horizontal=True,
            index=logic.YES_NO.index(request["reviewed_guide"]),
        )
        technical_contact = st.radio(
            "Is a technical contact available?", logic.YES_NO, horizontal=True,
            index=logic.YES_NO.index(request["technical_contact"]),
        )
        response = st.text_area("Message to the reviewer (optional)")
        resubmitted = st.form_submit_button("Resubmit request", type="primary")

    if not resubmitted:
        return
    try:
        logic.resubmit_request(request, requests_list, {
            "intended_use": intended_use, "reviewed_guide": reviewed_guide,
            "technical_contact": technical_contact,
        }, response)
    except ValueError as err:
        st.error(str(err))
        return
    except logic.DataFileError as err:
        st.error(f"Your request could not be saved: {err}")
        return
    st.session_state["status_message"] = f"{rid} was resubmitted for review."
    st.rerun()


def show_status_page():
    """Check Request Status page: look up a request, reveal the key, or resubmit."""
    st.title("Check Request Status")
    try:
        catalog, _ = load_catalog_and_specs()
    except logic.DataFileError as err:
        show_data_error(err)

    message = st.session_state.pop("status_message", None)
    if message:
        st.success(message)

    # Pre-fill the ID box with the request the user just submitted or looked up.
    if "status_request_id" not in st.session_state:
        st.session_state["status_request_id"] = st.session_state.get("last_request_id", "")
    request_id = st.text_input("Request ID", placeholder="REQ-AB12CD", key="status_request_id")
    if not request_id:
        return
    try:
        requests_list = load_requests()
    except logic.DataFileError as err:
        show_data_error(err)
    request = logic.find_request(request_id, requests_list)
    if not request:
        st.error("Request not found. Check the ID (it looks like REQ-AB12CD).")
        return
    st.session_state["last_request_id"] = request["request_id"]
    reveal = False
    if request.get("sample_credential"):
        reveal = st.toggle("Reveal full key")
    show_request_summary(request, catalog, reveal)
    if request["status"] == logic.STATUS_NEEDS_INFO:
        show_resubmit_form(request, requests_list)


def show_admin_page():
    """Admin Review page: approve Submitted requests or ask for more info."""
    st.title("Admin Review")
    st.caption("Simulated reviewer view - in a real hub this page would require an admin login.")
    try:
        catalog, _ = load_catalog_and_specs()
        requests_list = load_requests()
    except logic.DataFileError as err:
        show_data_error(err)

    message = st.session_state.pop("admin_message", None)
    if message:
        st.success(message)

    waiting = logic.list_requests_by_status(requests_list, logic.STATUS_SUBMITTED)
    count_cols = st.columns(3)
    for col, status in zip(count_cols, (logic.STATUS_SUBMITTED, logic.STATUS_NEEDS_INFO,
                                        logic.STATUS_AVAILABLE)):
        col.metric(status, len(logic.list_requests_by_status(requests_list, status)))

    st.subheader(f"Waiting for review ({len(waiting)})")
    if not waiting:
        st.info("No requests are waiting for review.")
    for request in waiting:
        rid = request["request_id"]
        product_name = logic.get_product_name(request["product_id"], catalog)
        label = f"{rid} - {request['name']} ({request['organization']}) - {product_name} / {request['environment']}"
        if request.get("resubmission_count"):
            label += " - resubmitted"
        with st.expander(label):
            if request.get("previous_review_note"):
                st.info(f"**You previously asked:** {request['previous_review_note']}")
            if request.get("requester_response"):
                st.write(f"**Requester's response:** {request['requester_response']}")
            st.write(f"**Email:** {request['email']}")
            st.write(f"**Operations:** {', '.join(request['operations'])}")
            st.write(f"**Intended use:** {request['intended_use']}")
            st.write(f"**Reviewed guide:** {request['reviewed_guide']}  |  "
                     f"**Technical contact:** {request['technical_contact']}")
            note = st.text_area("Note to requester (for Needs Information)",
                                value=logic.suggest_review_note(request), key=f"note_{rid}")
            approve_col, info_col = st.columns(2)
            try:
                if approve_col.button("Approve", key=f"approve_{rid}", type="primary"):
                    logic.approve_request(request, requests_list)
                    st.session_state["admin_message"] = f"{rid} approved."
                    st.rerun()
                if info_col.button("Needs more information", key=f"info_{rid}"):
                    logic.request_more_info(request, requests_list, note)
                    st.session_state["admin_message"] = f"{rid} marked Needs Information."
                    st.rerun()
            except ValueError as err:
                st.error(str(err))
            except logic.DataFileError as err:
                st.error(f"Could not save the review: {err}")

    st.subheader("All requests")
    if requests_list:
        status_filter = st.selectbox(
            "Show", ["All statuses", logic.STATUS_SUBMITTED, logic.STATUS_NEEDS_INFO,
                     logic.STATUS_AVAILABLE],
        )
        shown = requests_list if status_filter == "All statuses" else \
            logic.list_requests_by_status(requests_list, status_filter)
        st.dataframe(
            [{"Request ID": r["request_id"], "Name": r["name"],
              "API": logic.get_product_name(r["product_id"], catalog),
              "Environment": r["environment"], "Status": r["status"],
              "Resubmissions": r.get("resubmission_count", 0)} for r in shown],
            hide_index=True, width="stretch",
        )
    else:
        st.write("No requests yet.")


HOME_PAGE = st.Page(show_home_page, title="Home", icon="🏠", default=True)
CATALOG_PAGE = st.Page(show_catalog_page, title="API Catalog", icon="📚", url_path="catalog")
REQUEST_PAGE = st.Page(show_request_page, title="Request Credentials", icon="🔑", url_path="request")
STATUS_PAGE = st.Page(show_status_page, title="Check Request Status", icon="🔎", url_path="status")
ADMIN_PAGE = st.Page(show_admin_page, title="Admin Review", icon="🛡️", url_path="admin")

st.navigation([HOME_PAGE, CATALOG_PAGE, REQUEST_PAGE, STATUS_PAGE, ADMIN_PAGE]).run()
