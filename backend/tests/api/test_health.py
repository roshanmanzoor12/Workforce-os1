from fastapi.testclient import TestClient
from app.main import app
def test_root():
    r=TestClient(app).get("/")
    assert r.status_code==200
