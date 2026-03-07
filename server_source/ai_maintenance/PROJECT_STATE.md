# PROJECT STATE

## What exists now
- FastAPI server with auth, hunter CRUD, combat, offline rewards, worldboss/PvP, admin, and IAP endpoints.
- Pytest suite currently passing.
- Spreadsheet package is reference-only and should NOT auto-sync into runtime.
- Goal is maintainable iteration with AI assistants.

## Source of truth
- Runtime behavior: code in `server_source/`
- Progress / roadmap / QA history: spreadsheet in `design_sheet/`

## Safe next changes
- Add more tests around reward abuse and balance curves.
- Add DTO examples for Unity client.
- Add clearer error codes and response envelopes if desired.

## Dangerous changes
- Replacing repository behavior without updating tests.
- Reintroducing spreadsheet runtime dependency.
- Large schema changes without migration notes.
