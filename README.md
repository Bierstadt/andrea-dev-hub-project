# Andrea Developer Hub Project

This project is a prototype developer hub that helps users learn about available APIs and the steps required to use them

## Project layout

- `main.py` - the Version 1 command-line app. Run with `python main.py`.
- `data/` - local JSON files used as the app's data store:
  - `catalog.json` - finance API products shown in the catalog
  - `api_specs.json` - simplified API operations per product
  - `requests.json` - saved credential requests (created/updated by the app)
- `docs/` - project specification and sketch PDFs
- `bugs.md` - running list of known bugs and how to reproduce them
- `hello.py`, `hello_CH.py` - earlier GitHub-workflow practice files

## Credential request statuses

1. **Submitted** - request saved after passing validation
2. **Needs Information** - review found the API guide wasn't reviewed or there is no technical contact
3. **Credentials Available** - review passed; a sample (fake) key is shown, masked

Use *Request Credentials → View existing request* with your request ID to run the simulated review.

