from tests.conftest import auth_header


def test_activity_empty(client, alif_token):
    resp = client.get("/activity", headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_activity_after_rule_created(client, alif_token):
    client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    resp = client.get("/activity", headers=auth_header(alif_token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    types = [a["type"] for a in data]
    assert "rule_created" in types


def test_activity_after_question_and_answer(client, alif_token, syifa_token):
    create = client.post("/questions", json={"text": "Q1"}, headers=auth_header(alif_token))
    qid = create.json()["id"]
    client.post(f"/questions/{qid}/answer", json={"text": "A1"}, headers=auth_header(alif_token))
    client.post(f"/questions/{qid}/answer", json={"text": "A2"}, headers=auth_header(syifa_token))

    resp = client.get("/activity", headers=auth_header(alif_token))
    data = resp.json()
    types = [a["type"] for a in data]
    assert "question_asked" in types
    assert "answer_submitted" in types
    assert "answers_revealed" in types


def test_activity_after_milestone_confirmed(client, alif_token, syifa_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]
    client.post(f"/milestones/{mid}/approve", headers=auth_header(syifa_token))

    resp = client.get("/activity", headers=auth_header(alif_token))
    data = resp.json()
    types = [a["type"] for a in data]
    assert "milestone_proposed" in types
    assert "milestone_confirmed" in types


def test_activity_limit_20(client, alif_token):
    for i in range(25):
        client.post("/rules", json={"title": f"R{i}", "description": f"D{i}"}, headers=auth_header(alif_token))
    resp = client.get("/activity", headers=auth_header(alif_token))
    assert len(resp.json()) <= 20
