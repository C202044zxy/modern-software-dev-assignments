def test_create_and_complete_action_item(client):
    payload = {"description": "Ship it"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["completed"] is False

    r = client.put(f"/action-items/{item['id']}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["completed"] is True

    r = client.get("/action-items/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1


# ---------------------------------------------------------------------------
# PUT /action-items/{item_id}/complete — 404 for non-existent id
# ---------------------------------------------------------------------------


def test_complete_nonexistent_action_item_returns_404(client):
    r = client.put("/action-items/99999/complete")
    assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# POST /action-items/ — validation: non-empty description required
# ---------------------------------------------------------------------------


def test_create_action_item_empty_description_returns_422(client):
    r = client.post("/action-items/", json={"description": ""})
    assert r.status_code == 422, r.text
