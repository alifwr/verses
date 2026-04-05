from app.models import InviteCode, User


def test_me_authenticated(alif_client):
    resp = alif_client.get("/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "alif@test.com"
    assert data["display_name"] == "Alif"
    assert data["has_partner"] is True
    assert data["partner"]["display_name"] == "Syifa"


def test_me_unauthenticated(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 403


def test_create_invite_already_paired(alif_client):
    resp = alif_client.post("/auth/invite")
    assert resp.status_code == 400
    assert "already have a partner" in resp.json()["detail"]


def test_create_and_accept_invite(db):
    """Test full invite flow with two unpaired users."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.supabase_auth import get_current_user
    from app.database import get_db

    user_a = User(supabase_uid="test-uid-a", email="a@test.com", display_name="A")
    user_b = User(supabase_uid="test-uid-b", email="b@test.com", display_name="B")
    db.add(user_a)
    db.add(user_b)
    db.commit()
    db.refresh(user_a)
    db.refresh(user_b)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # User A creates invite
    app.dependency_overrides[get_current_user] = lambda: user_a
    with TestClient(app) as c:
        resp = c.post("/auth/invite")
        assert resp.status_code == 201
        code = resp.json()["code"]
        assert resp.json()["is_used"] is False

    # User B accepts invite
    app.dependency_overrides[get_current_user] = lambda: user_b
    with TestClient(app) as c:
        resp = c.post("/auth/accept-invite", json={"code": code})
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_partner"] is True
        assert data["partner"]["display_name"] == "A"

    # Verify both are paired
    db.refresh(user_a)
    db.refresh(user_b)
    assert user_a.partner_id == user_b.id
    assert user_b.partner_id == user_a.id


def test_accept_own_invite(db):
    """Cannot accept your own invite."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.supabase_auth import get_current_user
    from app.database import get_db

    user_a = User(supabase_uid="test-uid-own", email="own@test.com", display_name="Own")
    db.add(user_a)
    db.commit()
    db.refresh(user_a)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user_a

    with TestClient(app) as c:
        resp = c.post("/auth/invite")
        code = resp.json()["code"]
        resp = c.post("/auth/accept-invite", json={"code": code})
        assert resp.status_code == 400
        assert "own invite" in resp.json()["detail"]
