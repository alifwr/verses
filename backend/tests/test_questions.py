def test_create_question(alif_client):
    resp = alif_client.post(
        "/questions",
        json={"text": "Where should we live?"},
    )
    assert resp.status_code == 201
    assert resp.json()["text"] == "Where should we live?"


def test_list_questions(alif_client):
    alif_client.post("/questions", json={"text": "Q1"})
    resp = alif_client.get("/questions")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_double_blind_hides_partner_answer(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    create = client.post("/questions", json={"text": "Q1"})
    qid = create.json()["id"]

    # Switch to syifa to answer
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    client.post(f"/questions/{qid}/answer", json={"text": "Syifa's answer"})

    # Switch back to alif - should NOT see Syifa's answer (hasn't answered yet)
    app.dependency_overrides[get_current_user] = lambda: alif_user
    resp = client.get(f"/questions/{qid}")
    data = resp.json()
    assert data["my_answer"] is None
    assert data["partner_answer"] is None  # Hidden!


def test_double_blind_reveals_after_both_answer(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    create = client.post("/questions", json={"text": "Q1"})
    qid = create.json()["id"]

    # Switch to syifa to answer
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    client.post(f"/questions/{qid}/answer", json={"text": "Syifa's answer"})

    # Switch back to alif to answer
    app.dependency_overrides[get_current_user] = lambda: alif_user
    client.post(f"/questions/{qid}/answer", json={"text": "Alif's answer"})

    # Now Alif should see both
    resp = client.get(f"/questions/{qid}")
    data = resp.json()
    assert data["my_answer"]["text"] == "Alif's answer"
    assert data["partner_answer"]["text"] == "Syifa's answer"


def test_cannot_answer_twice(alif_client):
    create = alif_client.post("/questions", json={"text": "Q1"})
    qid = create.json()["id"]
    alif_client.post(f"/questions/{qid}/answer", json={"text": "A1"})
    resp = alif_client.post(f"/questions/{qid}/answer", json={"text": "A2"})
    assert resp.status_code == 400
