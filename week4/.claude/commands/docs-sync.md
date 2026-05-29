---
description: Sync docs/API.md with the live FastAPI OpenAPI schema and list route deltas
argument-hint: "(no args)"
allowed-tools: Bash(PYTHONPATH=. python:*), Read, Write, Edit
---

Keep `docs/API.md` in sync with the actual API surface defined by the FastAPI app. Run from the `week4/` directory.

## Steps

1. **Generate the current OpenAPI schema** without starting a server, by importing the app:

   ```bash
   PYTHONPATH=. python -c "import json; from backend.app.main import app; print(json.dumps(app.openapi(), indent=2))" > /tmp/openapi.json
   ```

2. **Read the existing docs** at `docs/API.md` (it may not exist yet — that's fine, you'll create it).

3. **Compute route deltas** by comparing the `paths` + methods in the schema against what `docs/API.md` currently documents:
   - **Added**: routes in the schema but missing from the docs.
   - **Removed**: routes documented but no longer in the schema.
   - **Changed**: same path+method but different summary, params, request body, or responses.

4. **Update `docs/API.md`** so every endpoint is documented. For each route include: method + path, summary/description, path & query params, request body schema (if any), and the success response shape. Group endpoints by tag/router (`notes`, `action-items`). Keep it readable Markdown — do not paste raw JSON.

## Output

- A diff-like summary with three sections: **Added**, **Removed**, **Changed** (each as a bullet list of `METHOD /path`).
- A short **TODOs** list for anything that needs a human decision (e.g. undocumented behavior, ambiguous response shapes).
- Confirm whether `docs/API.md` was created or edited.

## Safety

Only write to `docs/API.md`. Do not touch source code, routers, or schemas.
