def test_activity_empty(alif_client):
    resp = alif_client.get("/activity")
    assert resp.status_code == 200
    assert resp.json() == []


def test_activity_after_rule_created(alif_client):
    alif_client.post("/rules", json={"title": "R1", "description": "D1"})
    resp = alif_client.get("/activity")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    types = [a["type"] for a in data]
    assert "rule_created" in types


def test_activity_after_question_and_answer(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    create = client.post("/questions", json={"text": "Q1"})
    qid = create.json()["id"]
    client.post(f"/questions/{qid}/answer", json={"text": "A1"})

    # Switch to syifa
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    client.post(f"/questions/{qid}/answer", json={"text": "A2"})

    # Switch back to alif to check activity
    app.dependency_overrides[get_current_user] = lambda: alif_user
    resp = client.get("/activity")
    data = resp.json()
    types = [a["type"] for a in data]
    assert "question_asked" in types
    assert "answer_submitted" in types
    assert "answers_revealed" in types


def test_activity_after_milestone_confirmed(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    create = client.post("/milestones", json={"title": "M1", "description": "D1"})
    mid = create.json()["id"]

    # Switch to syifa to approve
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    client.post(f"/milestones/{mid}/approve")

    # Switch back to alif to check activity
    app.dependency_overrides[get_current_user] = lambda: alif_user
    resp = client.get("/activity")
    data = resp.json()
    types = [a["type"] for a in data]
    assert "milestone_proposed" in types
    assert "milestone_confirmed" in types


def test_activity_limit_20(alif_client):
    for i in range(25):
        alif_client.post("/rules", json={"title": f"R{i}", "description": f"D{i}"})
    resp = alif_client.get("/activity")
    assert len(resp.json()) <= 20
