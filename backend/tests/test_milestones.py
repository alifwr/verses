from tests.conftest import auth_header


def test_create_milestone(client, alif_token):
    resp = client.post(
        "/milestones",
        json={"title": "Get engaged", "description": "Propose formally", "target_date": "2027-01-01"},
        headers=auth_header(alif_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Get engaged"
    assert data["is_confirmed"] is False


def test_list_milestones(client, alif_token):
    client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    resp = client.get("/milestones", headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_approve_milestone_mutual(client, alif_token, syifa_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]

    client.post(f"/milestones/{mid}/approve", headers=auth_header(alif_token))
    resp = client.get("/milestones", headers=auth_header(alif_token))
    m = [x for x in resp.json() if x["id"] == mid][0]
    assert m["is_approved_by_me"] is True
    assert m["is_confirmed"] is False

    client.post(f"/milestones/{mid}/approve", headers=auth_header(syifa_token))
    resp = client.get("/milestones", headers=auth_header(alif_token))
    m = [x for x in resp.json() if x["id"] == mid][0]
    assert m["is_confirmed"] is True


def test_update_milestone(client, alif_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]
    resp = client.patch(f"/milestones/{mid}", json={"is_completed": True}, headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert resp.json()["is_completed"] is True


def test_delete_milestone_by_proposer(client, alif_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]
    resp = client.delete(f"/milestones/{mid}", headers=auth_header(alif_token))
    assert resp.status_code == 200


def test_cannot_delete_confirmed_milestone(client, alif_token, syifa_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]
    client.post(f"/milestones/{mid}/approve", headers=auth_header(alif_token))
    client.post(f"/milestones/{mid}/approve", headers=auth_header(syifa_token))
    resp = client.delete(f"/milestones/{mid}", headers=auth_header(alif_token))
    assert resp.status_code == 400
