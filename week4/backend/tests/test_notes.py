def test_create_and_list_notes(client):
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"

    r = client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get("/notes/search/")
    assert r.status_code == 200

    r = client.get("/notes/search/", params={"q": "Hello"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1


# ---------------------------------------------------------------------------
# GET /notes/search/ — case-insensitive search
# ---------------------------------------------------------------------------


def test_search_is_case_insensitive_lowercase_query(client):
    # Note title contains "Hello" (mixed case); searching with all-lowercase must match.
    r = client.post("/notes/", json={"title": "Hello World", "content": "Some content"})
    assert r.status_code == 201, r.text

    r = client.get("/notes/search/", params={"q": "hello"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1, "Lowercase query 'hello' should match note with title 'Hello World'"


def test_search_is_case_insensitive_uppercase_query(client):
    # Note content contains lowercase "hello"; searching with all-uppercase must match.
    r = client.post("/notes/", json={"title": "My note", "content": "hello from the content"})
    assert r.status_code == 201, r.text

    r = client.get("/notes/search/", params={"q": "HELLO"})
    assert r.status_code == 200
    items = r.json()
    assert (
        len(items) >= 1
    ), "Uppercase query 'HELLO' should match note with content 'hello from the content'"


# ---------------------------------------------------------------------------
# POST /notes/ — validation: non-empty title and content required
# ---------------------------------------------------------------------------


def test_create_note_empty_title_returns_422(client):
    r = client.post("/notes/", json={"title": "", "content": "Valid content"})
    assert r.status_code == 422, r.text


def test_create_note_empty_content_returns_422(client):
    r = client.post("/notes/", json={"title": "Valid title", "content": ""})
    assert r.status_code == 422, r.text


# ---------------------------------------------------------------------------
# PUT /notes/{note_id} — edit a note
# ---------------------------------------------------------------------------


def test_update_note_returns_200_with_updated_fields(client):
    r = client.post("/notes/", json={"title": "Original", "content": "Old content"})
    assert r.status_code == 201, r.text
    note_id = r.json()["id"]

    r = client.put(f"/notes/{note_id}", json={"title": "Updated", "content": "New content"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["id"] == note_id
    assert data["title"] == "Updated"
    assert data["content"] == "New content"


def test_update_note_persists_change(client):
    r = client.post("/notes/", json={"title": "Before", "content": "Before content"})
    assert r.status_code == 201, r.text
    note_id = r.json()["id"]

    client.put(f"/notes/{note_id}", json={"title": "After", "content": "After content"})

    r = client.get(f"/notes/{note_id}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["title"] == "After"
    assert data["content"] == "After content"


def test_update_nonexistent_note_returns_404(client):
    r = client.put("/notes/99999", json={"title": "X", "content": "Y"})
    assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# DELETE /notes/{note_id} — delete a note
# ---------------------------------------------------------------------------


def test_delete_note_returns_204(client):
    r = client.post("/notes/", json={"title": "To Delete", "content": "Bye"})
    assert r.status_code == 201, r.text
    note_id = r.json()["id"]

    r = client.delete(f"/notes/{note_id}")
    assert r.status_code == 204, r.text


def test_delete_note_removes_it(client):
    r = client.post("/notes/", json={"title": "Gone", "content": "Soon gone"})
    assert r.status_code == 201, r.text
    note_id = r.json()["id"]

    client.delete(f"/notes/{note_id}")

    r = client.get(f"/notes/{note_id}")
    assert r.status_code == 404, r.text


def test_delete_nonexistent_note_returns_404(client):
    r = client.delete("/notes/99999")
    assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# POST /notes/{note_id}/extract — turn a note into action items
# ---------------------------------------------------------------------------


def test_extract_creates_action_items_from_note(client):
    content = "Some context\n- TODO: write docs\n- Ship it!\nNot actionable"
    r = client.post("/notes/", json={"title": "Standup", "content": content})
    assert r.status_code == 201, r.text
    note_id = r.json()["id"]

    r = client.post(f"/notes/{note_id}/extract")
    assert r.status_code == 201, r.text
    items = r.json()
    descriptions = {item["description"] for item in items}
    assert "TODO: write docs" in descriptions
    assert "Ship it!" in descriptions
    assert all(item["completed"] is False for item in items)

    # The extracted items are persisted and listable.
    r = client.get("/action-items/")
    assert r.status_code == 200
    listed = {item["description"] for item in r.json()}
    assert {"TODO: write docs", "Ship it!"} <= listed


def test_extract_nonexistent_note_returns_404(client):
    r = client.post("/notes/99999/extract")
    assert r.status_code == 404, r.text
