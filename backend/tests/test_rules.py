from tests.conftest import auth_header


def test_create_rule(client, alif_token):
    resp = client.post(
        "/rules",
        json={"title": "No late calls", "description": "Calls end by 9 PM"},
        headers=auth_header(alif_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "No late calls"
    assert data["is_sealed"] is False
    assert data["is_agreed_by_me"] is True
    assert data["is_agreed_by_partner"] is False


def test_list_rules(client, alif_token):
    client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    resp = client.get("/rules", headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_partner_sign_seals_rule(client, alif_token, syifa_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]

    resp = client.get("/rules", headers=auth_header(alif_token))
    rule = [r for r in resp.json() if r["id"] == rule_id][0]
    assert rule["is_agreed_by_me"] is True
    assert rule["is_agreed_by_partner"] is False
    assert rule["is_sealed"] is False

    resp = client.post(f"/rules/{rule_id}/sign", headers=auth_header(syifa_token))
    assert resp.status_code == 200

    resp = client.get("/rules", headers=auth_header(alif_token))
    rule = [r for r in resp.json() if r["id"] == rule_id][0]
    assert rule["is_sealed"] is True


def test_proposer_cannot_double_sign(client, alif_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]
    resp = client.post(f"/rules/{rule_id}/sign", headers=auth_header(alif_token))
    assert resp.status_code == 400


def test_delete_rule_by_proposer(client, alif_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]
    resp = client.delete(f"/rules/{rule_id}", headers=auth_header(alif_token))
    assert resp.status_code == 200


def test_cannot_delete_sealed_rule(client, alif_token, syifa_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]
    client.post(f"/rules/{rule_id}/sign", headers=auth_header(syifa_token))
    resp = client.delete(f"/rules/{rule_id}", headers=auth_header(alif_token))
    assert resp.status_code == 400


def test_cannot_delete_rule_by_non_proposer(client, alif_token, syifa_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]
    resp = client.delete(f"/rules/{rule_id}", headers=auth_header(syifa_token))
    assert resp.status_code == 403
