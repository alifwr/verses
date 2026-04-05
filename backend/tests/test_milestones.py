def test_create_milestone(alif_client):
    resp = alif_client.post(
        "/milestones",
        json={"title": "Get engaged", "description": "Propose formally", "target_date": "2027-01-01"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Get engaged"
    assert data["is_confirmed"] is False
    assert data["is_approved_by_me"] is True
    assert data["is_approved_by_partner"] is False


def test_list_milestones(alif_client):
    alif_client.post("/milestones", json={"title": "M1", "description": "D1"})
    resp = alif_client.get("/milestones")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_partner_approve_confirms_milestone(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    create = client.post("/milestones", json={"title": "M1", "description": "D1"})
    mid = create.json()["id"]

    resp = client.get("/milestones")
    m = [x for x in resp.json() if x["id"] == mid][0]
    assert m["is_approved_by_me"] is True
    assert m["is_confirmed"] is False

    # Switch to syifa to approve
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    client.post(f"/milestones/{mid}/approve")

    # Switch back to alif to check
    app.dependency_overrides[get_current_user] = lambda: alif_user
    resp = client.get("/milestones")
    m = [x for x in resp.json() if x["id"] == mid][0]
    assert m["is_confirmed"] is True


def test_proposer_cannot_double_approve(alif_client):
    create = alif_client.post("/milestones", json={"title": "M1", "description": "D1"})
    mid = create.json()["id"]
    resp = alif_client.post(f"/milestones/{mid}/approve")
    assert resp.status_code == 400


def test_update_milestone(alif_client):
    create = alif_client.post("/milestones", json={"title": "M1", "description": "D1"})
    mid = create.json()["id"]
    resp = alif_client.patch(f"/milestones/{mid}", json={"is_completed": True})
    assert resp.status_code == 200
    assert resp.json()["is_completed"] is True


def test_delete_milestone_by_proposer(alif_client):
    create = alif_client.post("/milestones", json={"title": "M1", "description": "D1"})
    mid = create.json()["id"]
    resp = alif_client.delete(f"/milestones/{mid}")
    assert resp.status_code == 200


def test_cannot_delete_confirmed_milestone(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    create = client.post("/milestones", json={"title": "M1", "description": "D1"})
    mid = create.json()["id"]

    # Switch to syifa to approve
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    client.post(f"/milestones/{mid}/approve")

    # Switch back to alif to try delete
    app.dependency_overrides[get_current_user] = lambda: alif_user
    resp = client.delete(f"/milestones/{mid}")
    assert resp.status_code == 400
