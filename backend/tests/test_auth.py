from tests.conftest import auth_header


def test_login_success(client):
    resp = client.post("/auth/login", data={"username": "alif", "password": "verse2024"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    resp = client.post("/auth/login", data={"username": "alif", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = client.post("/auth/login", data={"username": "unknown", "password": "verse2024"})
    assert resp.status_code == 401


def test_me_authenticated(client, alif_token):
    resp = client.get("/auth/me", headers=auth_header(alif_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "alif"
    assert data["display_name"] == "Alif"
    assert "partner" in data


def test_me_unauthenticated(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_refresh_token(client, alif_token):
    login_resp = client.post("/auth/login", data={"username": "alif", "password": "verse2024"})
    refresh = login_resp.json()["refresh_token"]
    resp = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
