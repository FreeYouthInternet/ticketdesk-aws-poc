import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_unauthenticated_redirect():
    res = client.get("/", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["location"] == "/login"

def test_login_invalid():
    res = client.post("/login", data={"username": "admin", "password": "wrong"})
    assert res.status_code == 401

def test_full_ticket_workflow():
    res = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=False)
    assert res.status_code == 302
    cookies = res.cookies

    res = client.post(
        "/tickets",
        data={"title": "VPN Issue", "description": "Cannot connect to office VPN"},
        files={"file": ("error.txt", b"VPN timeout log", "text/plain")},
        cookies=cookies,
        follow_redirects=False
    )
    assert res.status_code == 302

    res = client.get("/", cookies=cookies)
    assert res.status_code == 200
    assert "VPN Issue" in res.text

    res = client.post("/tickets/1/status", data={"status": "Resolved"}, cookies=cookies, follow_redirects=False)
    assert res.status_code == 302
