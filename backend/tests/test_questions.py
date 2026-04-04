from tests.conftest import auth_header


def test_create_question(client, alif_token):
    resp = client.post(
        "/questions",
        json={"text": "Where should we live?"},
        headers=auth_header(alif_token),
    )
    assert resp.status_code == 201
    assert resp.json()["text"] == "Where should we live?"


def test_list_questions(client, alif_token):
    client.post("/questions", json={"text": "Q1"}, headers=auth_header(alif_token))
    resp = client.get("/questions", headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_double_blind_hides_partner_answer(client, alif_token, syifa_token):
    create = client.post("/questions", json={"text": "Q1"}, headers=auth_header(alif_token))
    qid = create.json()["id"]

    # Syifa answers
    client.post(f"/questions/{qid}/answer", json={"text": "Syifa's answer"}, headers=auth_header(syifa_token))

    # Alif checks - should NOT see Syifa's answer (hasn't answered yet)
    resp = client.get(f"/questions/{qid}", headers=auth_header(alif_token))
    data = resp.json()
    assert data["my_answer"] is None
    assert data["partner_answer"] is None  # Hidden!


def test_double_blind_reveals_after_both_answer(client, alif_token, syifa_token):
    create = client.post("/questions", json={"text": "Q1"}, headers=auth_header(alif_token))
    qid = create.json()["id"]

    client.post(f"/questions/{qid}/answer", json={"text": "Syifa's answer"}, headers=auth_header(syifa_token))
    client.post(f"/questions/{qid}/answer", json={"text": "Alif's answer"}, headers=auth_header(alif_token))

    # Now Alif should see both
    resp = client.get(f"/questions/{qid}", headers=auth_header(alif_token))
    data = resp.json()
    assert data["my_answer"]["text"] == "Alif's answer"
    assert data["partner_answer"]["text"] == "Syifa's answer"


def test_cannot_answer_twice(client, alif_token):
    create = client.post("/questions", json={"text": "Q1"}, headers=auth_header(alif_token))
    qid = create.json()["id"]
    client.post(f"/questions/{qid}/answer", json={"text": "A1"}, headers=auth_header(alif_token))
    resp = client.post(f"/questions/{qid}/answer", json={"text": "A2"}, headers=auth_header(alif_token))
    assert resp.status_code == 400
