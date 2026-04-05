def test_create_talk(alif_client):
    resp = alif_client.post("/talks", json={"title": "Discuss wedding venue"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Discuss wedding venue"
    assert data["status"] == "queued"
    assert data["proposer_name"] == "Alif"
    assert data["note_count"] == 0


def test_list_talks(alif_client):
    alif_client.post("/talks", json={"title": "Talk A"})
    alif_client.post("/talks", json={"title": "Talk B"})
    resp = alif_client.get("/talks")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_talks_queued_first(alif_client):
    alif_client.post("/talks", json={"title": "Old talk"})
    resp2 = alif_client.post("/talks", json={"title": "New talk"})
    talk_id = resp2.json()["id"]
    alif_client.patch(f"/talks/{talk_id}", json={"status": "discussed"})

    resp = alif_client.get("/talks")
    talks = resp.json()
    assert talks[0]["status"] == "queued"
    assert talks[1]["status"] == "discussed"


def test_update_talk_status(alif_client):
    resp = alif_client.post("/talks", json={"title": "Topic"})
    talk_id = resp.json()["id"]

    resp = alif_client.patch(f"/talks/{talk_id}", json={"status": "discussed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "discussed"


def test_update_talk_status_follow_up(alif_client):
    resp = alif_client.post("/talks", json={"title": "Topic"})
    talk_id = resp.json()["id"]

    resp = alif_client.patch(f"/talks/{talk_id}", json={"status": "follow_up"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "follow_up"


def test_update_talk_invalid_status(alif_client):
    resp = alif_client.post("/talks", json={"title": "Topic"})
    talk_id = resp.json()["id"]

    resp = alif_client.patch(f"/talks/{talk_id}", json={"status": "invalid"})
    assert resp.status_code == 400


def test_partner_can_update_status(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    resp = client.post("/talks", json={"title": "Topic"})
    talk_id = resp.json()["id"]

    # Switch to syifa
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    resp = client.patch(f"/talks/{talk_id}", json={"status": "discussed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "discussed"


def test_only_proposer_can_edit_title(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    resp = client.post("/talks", json={"title": "Topic"})
    talk_id = resp.json()["id"]

    # Switch to syifa
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    resp = client.patch(f"/talks/{talk_id}", json={"title": "Changed"})
    assert resp.status_code == 403


def test_delete_talk(alif_client):
    resp = alif_client.post("/talks", json={"title": "Topic"})
    talk_id = resp.json()["id"]

    resp = alif_client.delete(f"/talks/{talk_id}")
    assert resp.status_code == 200

    resp = alif_client.get("/talks")
    assert len(resp.json()) == 0


def test_only_proposer_can_delete(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    resp = client.post("/talks", json={"title": "Topic"})
    talk_id = resp.json()["id"]

    # Switch to syifa
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    resp = client.delete(f"/talks/{talk_id}")
    assert resp.status_code == 403


def test_cannot_delete_non_queued_talk(alif_client):
    resp = alif_client.post("/talks", json={"title": "Topic"})
    talk_id = resp.json()["id"]
    alif_client.patch(f"/talks/{talk_id}", json={"status": "discussed"})

    resp = alif_client.delete(f"/talks/{talk_id}")
    assert resp.status_code == 400


def test_add_note(alif_client):
    resp = alif_client.post("/talks", json={"title": "Topic"})
    talk_id = resp.json()["id"]

    resp = alif_client.post(f"/talks/{talk_id}/notes", json={"text": "My thoughts"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["note_count"] == 1
    assert data["notes"][0]["text"] == "My thoughts"


def test_partner_can_add_note(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    resp = client.post("/talks", json={"title": "Topic"})
    talk_id = resp.json()["id"]

    client.post(f"/talks/{talk_id}/notes", json={"text": "Alif note"})

    # Switch to syifa
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    resp = client.post(f"/talks/{talk_id}/notes", json={"text": "Syifa note"})
    assert resp.json()["note_count"] == 2


def test_delete_own_note(alif_client):
    resp = alif_client.post("/talks", json={"title": "Topic"})
    talk_id = resp.json()["id"]

    resp = alif_client.post(f"/talks/{talk_id}/notes", json={"text": "Note"})
    note_id = resp.json()["notes"][0]["id"]

    resp = alif_client.delete(f"/talks/{talk_id}/notes/{note_id}")
    assert resp.status_code == 200


def test_cannot_delete_partner_note(client, alif_user, syifa_user):
    from app.main import app
    from app.supabase_auth import get_current_user

    # Act as alif
    app.dependency_overrides[get_current_user] = lambda: alif_user
    resp = client.post("/talks", json={"title": "Topic"})
    talk_id = resp.json()["id"]

    resp = client.post(f"/talks/{talk_id}/notes", json={"text": "Alif note"})
    note_id = resp.json()["notes"][0]["id"]

    # Switch to syifa
    app.dependency_overrides[get_current_user] = lambda: syifa_user
    resp = client.delete(f"/talks/{talk_id}/notes/{note_id}")
    assert resp.status_code == 403
