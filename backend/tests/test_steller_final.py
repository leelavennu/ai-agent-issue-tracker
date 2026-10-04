def test_empty_title_returns_400(client):
    assert client.post("/issues", json={"title": "", "description": "x"}).status_code == 400
def test_201_char_returns_400(client):
    assert client.post("/issues", json={"title": "a"*201, "description": "x"}).status_code == 400
def test_duplicate_409(client):
    client.post("/issues", json={"title": "dup-test", "description": "x"})
    assert client.post("/issues", json={"title": "dup-test", "description": "x"}).status_code == 409
def test_missing_role_401(client):
    c = client.post("/issues", json={"title": "del-401", "description": "x"})
    assert client.delete(f"/issues/{c.json()['id']}").status_code == 401
def test_user_role_403(client):
    c = client.post("/issues", json={"title": "del-403", "description": "x"})
    assert client.delete(f"/issues/{c.json()['id']}", headers={"X-User-Role": "user"}).status_code == 403
def test_admin_delete_200(client):
    c = client.post("/issues", json={"title": "del-admin", "description": "x"})
    assert client.delete(f"/issues/{c.json()['id']}", headers={"X-User-Role": "admin"}).status_code == 204
def test_special_chars(client):
    assert client.post("/issues", json={"title": "<script>😀' OR 1=1", "description": "x"}).status_code == 201
def test_filter_search_pagination(client):
    assert client.get("/issues?status=open").status_code == 200
    assert client.get("/issues?search=alpha").status_code == 200
