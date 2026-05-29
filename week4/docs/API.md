# API Reference

Auto-synced with the FastAPI app's OpenAPI schema (`backend/app/main.py`). Regenerate with the `/docs-sync` command.

All request/response bodies are JSON. Validation failures return **422** with an `HTTPValidationError` body (see [Schemas](#schemas)).

Base URL: `/` (interactive docs available at `/docs`).

## Root

### `GET /`

Serves the frontend single-page app (`frontend/index.html`).

- **Params:** none
- **Response `200`:** HTML page (not JSON).

## Notes

Router prefix: `/notes` (tag `notes`).

### `GET /notes/`

List all notes.

- **Params:** none
- **Response `200`:** array of [`NoteRead`](#noteread)

### `POST /notes/`

Create a note.

- **Request body:** [`NoteCreate`](#notecreate)
- **Response `201`:** [`NoteRead`](#noteread)
- **Response `422`:** [`HTTPValidationError`](#httpvalidationerror)

### `GET /notes/search/`

Search notes by substring. Matches notes whose `title` **or** `content` contains `q` (case-sensitive substring match). When `q` is omitted or empty, returns all notes.

> Declared before `GET /notes/{note_id}` so the literal `search/` path is not captured by the `{note_id}` converter.

- **Query params:**
  - `q` *(string, optional)* — search term.
- **Response `200`:** array of [`NoteRead`](#noteread)
- **Response `422`:** [`HTTPValidationError`](#httpvalidationerror)

### `GET /notes/{note_id}`

Fetch a single note by id.

- **Path params:**
  - `note_id` *(integer, required)*
- **Response `200`:** [`NoteRead`](#noteread)
- **Response `404`:** `{"detail": "Note not found"}` *(not present in the OpenAPI schema; raised via `HTTPException`)*
- **Response `422`:** [`HTTPValidationError`](#httpvalidationerror)

## Action Items

Router prefix: `/action-items` (tag `action_items`).

### `GET /action-items/`

List all action items.

- **Params:** none
- **Response `200`:** array of [`ActionItemRead`](#actionitemread)

### `POST /action-items/`

Create an action item. `completed` is always initialized to `false`.

- **Request body:** [`ActionItemCreate`](#actionitemcreate)
- **Response `201`:** [`ActionItemRead`](#actionitemread)
- **Response `422`:** [`HTTPValidationError`](#httpvalidationerror)

### `PUT /action-items/{item_id}/complete`

Mark an action item as completed (`completed = true`).

- **Path params:**
  - `item_id` *(integer, required)*
- **Response `200`:** [`ActionItemRead`](#actionitemread)
- **Response `404`:** `{"detail": "Action item not found"}` *(not present in the OpenAPI schema; raised via `HTTPException`)*
- **Response `422`:** [`HTTPValidationError`](#httpvalidationerror)

## Schemas

### NoteCreate

| Field | Type | Required |
|-------|------|----------|
| `title` | string | yes |
| `content` | string | yes |

### NoteRead

| Field | Type | Required |
|-------|------|----------|
| `id` | integer | yes |
| `title` | string | yes |
| `content` | string | yes |

### ActionItemCreate

| Field | Type | Required |
|-------|------|----------|
| `description` | string | yes |

### ActionItemRead

| Field | Type | Required |
|-------|------|----------|
| `id` | integer | yes |
| `description` | string | yes |
| `completed` | boolean | yes |

### HTTPValidationError

| Field | Type | Required |
|-------|------|----------|
| `detail` | array of [`ValidationError`](#validationerror) | no |

### ValidationError

| Field | Type | Required |
|-------|------|----------|
| `loc` | array of (string \| integer) | yes |
| `msg` | string | yes |
| `type` | string | yes |
