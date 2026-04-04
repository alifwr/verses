from tests.conftest import auth_header


def test_create_talk(client, alif_token):
    resp = client.post("/talks", json={"title": "Discuss wedding venue"}, headers=auth_header(alif_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Discuss wedding venue"
    assert data["status"] == "queued"
    assert data["proposer_name"] == "Alif"
    assert data["note_count"] == 0


def test_list_talks(client, alif_token):
    client.post("/talks", json={"title": "Talk A"}, headers=auth_header(alif_token))
    client.post("/talks", json={"title": "Talk B"}, headers=auth_header(alif_token))
    resp = client.get("/talks", headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_talks_queued_first(client, alif_token):
    client.post("/talks", json={"title": "Old talk"}, headers=auth_header(alif_token))
    resp2 = client.post("/talks", json={"title": "New talk"}, headers=auth_header(alif_token))
    talk_id = resp2.json()["id"]
    client.patch(f"/talks/{talk_id}", json={"status": "discussed"}, headers=auth_header(alif_token))

    resp = client.get("/talks", headers=auth_header(alif_token))
    talks = resp.json()
    assert talks[0]["status"] == "queued"
    assert talks[1]["status"] == "discussed"


def test_update_talk_status(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.patch(f"/talks/{talk_id}", json={"status": "discussed"}, headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "discussed"


def test_update_talk_status_follow_up(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.patch(f"/talks/{talk_id}", json={"status": "follow_up"}, headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "follow_up"


def test_update_talk_invalid_status(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.patch(f"/talks/{talk_id}", json={"status": "invalid"}, headers=auth_header(alif_token))
    assert resp.status_code == 400


def test_partner_can_update_status(client, alif_token, syifa_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.patch(f"/talks/{talk_id}", json={"status": "discussed"}, headers=auth_header(syifa_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "discussed"


def test_only_proposer_can_edit_title(client, alif_token, syifa_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.patch(f"/talks/{talk_id}", json={"title": "Changed"}, headers=auth_header(syifa_token))
    assert resp.status_code == 403


def test_delete_talk(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.delete(f"/talks/{talk_id}", headers=auth_header(alif_token))
    assert resp.status_code == 200

    resp = client.get("/talks", headers=auth_header(alif_token))
    assert len(resp.json()) == 0


def test_only_proposer_can_delete(client, alif_token, syifa_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.delete(f"/talks/{talk_id}", headers=auth_header(syifa_token))
    assert resp.status_code == 403


def test_cannot_delete_non_queued_talk(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]
    client.patch(f"/talks/{talk_id}", json={"status": "discussed"}, headers=auth_header(alif_token))

    resp = client.delete(f"/talks/{talk_id}", headers=auth_header(alif_token))
    assert resp.status_code == 400


def test_add_note(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.post(f"/talks/{talk_id}/notes", json={"text": "My thoughts"}, headers=auth_header(alif_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["note_count"] == 1
    assert data["notes"][0]["text"] == "My thoughts"


def test_partner_can_add_note(client, alif_token, syifa_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    client.post(f"/talks/{talk_id}/notes", json={"text": "Alif note"}, headers=auth_header(alif_token))
    resp = client.post(f"/talks/{talk_id}/notes", json={"text": "Syifa note"}, headers=auth_header(syifa_token))
    assert resp.json()["note_count"] == 2


def test_delete_own_note(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.post(f"/talks/{talk_id}/notes", json={"text": "Note"}, headers=auth_header(alif_token))
    note_id = resp.json()["notes"][0]["id"]

    resp = client.delete(f"/talks/{talk_id}/notes/{note_id}", headers=auth_header(alif_token))
    assert resp.status_code == 200


def test_cannot_delete_partner_note(client, alif_token, syifa_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.post(f"/talks/{talk_id}/notes", json={"text": "Alif note"}, headers=auth_header(alif_token))
    note_id = resp.json()["notes"][0]["id"]

    resp = client.delete(f"/talks/{talk_id}/notes/{note_id}", headers=auth_header(syifa_token))
    assert resp.status_code == 403
