def test_create_rule(alif_client):
    resp = alif_client.post(
        "/rules",
        json={"title": "No late calls", "description": "Calls end by 9 PM"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "No late calls"
    assert data["is_sealed"] is False
    assert data["is_agreed_by_me"] is True
    assert data["is_agreed_by_partner"] is False


def test_list_rules(alif_client):
    alif_client.post("/rules", json={"title": "R1", "description": "D1"})
    resp = alif_client.get("/rules")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_partner_sign_seals_rule(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    create = client.post("/rules", json={"title": "R1", "description": "D1"})
    rule_id = create.json()["id"]

    resp = client.get("/rules")
    rule = [r for r in resp.json() if r["id"] == rule_id][0]
    assert rule["is_agreed_by_me"] is True
    assert rule["is_agreed_by_partner"] is False
    assert rule["is_sealed"] is False

    # Switch to syifa
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    resp = client.post(f"/rules/{rule_id}/sign")
    assert resp.status_code == 200

    # Switch back to alif to check
    app.dependency_overrides[get_current_user] = lambda: alif_user
    resp = client.get("/rules")
    rule = [r for r in resp.json() if r["id"] == rule_id][0]
    assert rule["is_sealed"] is True


def test_proposer_cannot_double_sign(alif_client):
    create = alif_client.post("/rules", json={"title": "R1", "description": "D1"})
    rule_id = create.json()["id"]
    resp = alif_client.post(f"/rules/{rule_id}/sign")
    assert resp.status_code == 400


def test_delete_rule_by_proposer(alif_client):
    create = alif_client.post("/rules", json={"title": "R1", "description": "D1"})
    rule_id = create.json()["id"]
    resp = alif_client.delete(f"/rules/{rule_id}")
    assert resp.status_code == 200


def test_cannot_delete_sealed_rule(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    create = client.post("/rules", json={"title": "R1", "description": "D1"})
    rule_id = create.json()["id"]

    # Switch to syifa to sign
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    client.post(f"/rules/{rule_id}/sign")

    # Switch back to alif to try delete
    app.dependency_overrides[get_current_user] = lambda: alif_user
    resp = client.delete(f"/rules/{rule_id}")
    assert resp.status_code == 400


def test_cannot_delete_rule_by_non_proposer(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    create = client.post("/rules", json={"title": "R1", "description": "D1"})
    rule_id = create.json()["id"]

    # Switch to syifa to try delete
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    resp = client.delete(f"/rules/{rule_id}")
    assert resp.status_code == 403
