# Andrea Developer Hub Project

This project is a prototype developer hub that helps users learn about available APIs and the steps required to use them

## How to run

```
pip install -r requirements.txt
streamlit run app.py        # Version 2 web app
python main.py              # command-line version
python -m unittest test_hub_logic   # unit tests
```

## Project layout

- `app.py` - the Version 2 Streamlit app (Home, API Catalog, Request Credentials, Check Request Status, Admin Review). Pages are built with `st.navigation` in one file, so there is no `pages/` folder.
- `hub_logic.py` - shared "logic" functions (load data, search, validate, save, review). No `print()`/`input()`, so both apps can use them.
- `main.py` - the command-line version of the app. Run with `python main.py`.
- `test_hub_logic.py` - unit tests for `hub_logic.py`.
- `requirements.txt` - Python packages needed (Streamlit).
- `data/` - local JSON files used as the app's data store:
  - `catalog.json` - finance API products shown in the catalog
  - `api_specs.json` - simplified API operations per product
  - `requests.json` - saved credential requests (created/updated by the app)
- `docs/` - project spec (original and revised), V1 sketch, and Version 1 review (PDF + Word); `docs/img/` holds the review screenshots
- `bugs.md` - running list of known bugs and how to reproduce them
- `hello.py`, `hello_CH.py` - earlier GitHub-workflow practice files

## Credential request statuses

1. **Submitted** - request saved after passing validation; waiting for an admin
2. **Needs Information** - the admin sent it back with a note explaining what is missing
3. **Credentials Available** - the admin approved it; a sample (fake) key is shown, masked, with an option to reveal it

The review is done on the **Admin Review** page (or menu option 3 in `main.py`). The suggested note only mentions the readiness answers that were "no". Requesters check their status with their request ID.

If a request is Needs Information, the requester can update their intended use and readiness answers on the Check Request Status page (or after looking up the request in `main.py`), add an optional message, and resubmit it. It goes back to Submitted, and the admin sees the earlier note and the requester's response. A resubmission must change at least one answer or include a message.

