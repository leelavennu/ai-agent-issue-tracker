def test_accepts_valid_create_and_filter(client):
    created = client.post(
        "/issues",
        json={"title": "Verifier issue", "description": "contract test"},
    )
    assert created.status_code == 201
    assert client.get("/issues?status=open").status_code == 200


def test_accepts_admin_delete(client):
    created = client.post("/issues", json={"title": "Delete me"})
    assert created.status_code == 201
    assert client.delete(
        f"/issues/{created.json()['id']}",
        headers={"X-User-Role": "admin"},
    ).status_code == 204


def test_rejects_missing_role(client):
    created = client.post("/issues", json={"title": "Missing role"})
    assert client.delete(f"/issues/{created.json()['id']}").status_code == 401


def test_rejects_unsupported_role(client):
    created = client.post("/issues", json={"title": "Unsupported role"})
    assert client.delete(
        f"/issues/{created.json()['id']}",
        headers={"X-User-Role": "owner"},
    ).status_code == 401


def test_rejects_duplicate_title(client):
    assert client.post("/issues", json={"title": "Duplicate"}).status_code == 201
    assert client.post("/issues", json={"title": "Duplicate"}).status_code == 409


def test_rejects_missing_title(client):
    assert client.post("/issues", json={"title": ""}).status_code == 400


def test_rejects_unknown_id(client):
    assert client.get("/issues/999999").status_code == 404
