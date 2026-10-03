import os
import sys
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app, Base, engine, SessionLocal, Issue

client = TestClient(app)

def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_create_list_and_filter_issue():
    response = client.post("/issues", json={"title": "Fix login", "description": "OAuth", "priority": "high"})
    assert response.status_code == 201
    response = client.get("/issues?priority=high&search=OAuth")
    assert response.status_code == 200
    assert response.json()["total"] == 1

def test_validation_duplicate_and_invalid_id():
    assert client.post("/issues", json={"title": ""}).status_code == 422
    assert client.post("/issues", json={"title": "x" * 201}).status_code == 422
    assert client.post("/issues", json={"title": "Unique"}).status_code == 201
    assert client.post("/issues", json={"title": "Unique"}).status_code == 409
    assert client.get("/issues/999999").status_code == 404

def test_last_write_wins_warning_and_delete_auth():
    created = client.post("/issues", json={"title": "Concurrent"}).json()
    assert client.put(f"/issues/{created['id']}", json={"description": "first", "version": 1}).status_code == 200
    assert client.put(f"/issues/{created['id']}", json={"description": "stale", "version": 1}).status_code == 409
    assert client.delete(f"/issues/{created['id']}").status_code == 403
    assert client.delete(f"/issues/{created['id']}", headers={"X-User-Role": "admin"}).status_code == 204

def test_special_characters_are_stored_as_text():
    title = "<script>alert('x')</script> 🐍"
    response = client.post("/issues", json={"title": title, "description": "' OR 1=1; --"})
    assert response.status_code == 201
    assert client.get("/issues", params={"search": "script"}).json()["total"] == 1
