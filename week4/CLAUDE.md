# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`week4/` is a "developer's command center" starter app: a FastAPI + SQLite (SQLAlchemy) backend with a static, build-free frontend. It is the playground for the Week 4 assignment (`assignment.md`), whose goal is to build 2+ Claude Code automations (slash commands, `CLAUDE.md` files, SubAgents, MCP servers) and use them to extend this app. `docs/TASKS.md` is the backlog of intended enhancements; `writeup.md` documents the automations built.

## Commands

All commands are run from the `week4/` directory and rely on the `Makefile`, which sets `PYTHONPATH=.` (required — the backend uses package-relative imports rooted at `week4/`).

```bash
make run      # uvicorn backend.app.main:app --reload  (frontend at /, API docs at /docs)
make test     # pytest -q backend/tests
make format   # black . && ruff check . --fix
make lint     # ruff check .
make seed     # apply data/seed.sql into a fresh data/app.db
```

Run a single test: `PYTHONPATH=. pytest backend/tests/test_notes.py::test_name -q`

The conda env is `cs146s` (Python 3.12); dependencies are managed by Poetry at the repo root. Pre-commit (`pre-commit install`) runs black + ruff. Line length is 100; ruff ignores E501 and B008.

## Architecture

- **Entry point** `backend/app/main.py` — creates the `FastAPI` app, mounts `frontend/` at `/static`, serves `frontend/index.html` at `/`, and on startup calls `Base.metadata.create_all` + `apply_seed_if_needed()`. Routers are registered here.
- **Routers** `backend/app/routers/{notes,action_items}.py` — each defines an `APIRouter` with a prefix (`/notes`, `/action-items`) and is included in `main.py`. Add new endpoints to the matching router, or a new router file that `main.py` includes.
- **Persistence** `backend/app/db.py` — single SQLite engine at `DATABASE_PATH` (default `./data/app.db`). `get_db` is the FastAPI dependency (commit-on-success, rollback-on-exception); `get_session` is the equivalent context manager for non-request code. `apply_seed_if_needed()` runs `data/seed.sql` **only when the DB file does not yet exist** — to reseed, delete `data/app.db` first.
- **Models vs. schemas** — `models.py` holds SQLAlchemy ORM tables (`Note`, `ActionItem`); `schemas.py` holds Pydantic request/response models (`*Create`, `*Read`, the latter with `from_attributes = True`). Routers convert ORM rows with `SchemaRead.model_validate(row)`.
- **Services** `backend/app/services/extract.py` — pure functions (no DB), e.g. `extract_action_items` parses note text into candidate action items. Keep business logic here, testable in isolation.
- **Frontend** `frontend/{index.html,app.js,styles.css}` — vanilla JS that calls the JSON API; no bundler or Node toolchain.

### Gotchas

- **Route ordering**: `GET /notes/search/` is declared *before* `GET /notes/{note_id}` in `notes.py` so the literal path isn't captured by the `{note_id}` converter. Keep static/literal paths above parameterized ones.
- **Tests use an isolated DB**: `backend/tests/conftest.py` overrides `get_db` with a fresh temp-file SQLite engine per test via `app.dependency_overrides`, so tests never touch `data/app.db`. Write API tests against the `client` fixture (FastAPI `TestClient`).

## Workflow for adding/changing an endpoint

1. Add/update the Pydantic schema in `schemas.py` and the ORM model in `models.py` (and `data/seed.sql` if the schema changes).
2. Add the route to the relevant router; validate ORM → schema with `model_validate`.
3. Add a test in `backend/tests/` using the `client` fixture, then run `make test` and `make lint`.
