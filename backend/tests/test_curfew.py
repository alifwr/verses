from unittest.mock import patch
from datetime import datetime
from tests.conftest import auth_header


def test_write_allowed_during_day(client, alif_token):
    with patch("app.middleware.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 4, 4, 14, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        resp = client.post(
            "/rules",
            json={"title": "Test Rule", "description": "Test"},
            headers=auth_header(alif_token),
        )
        assert resp.status_code != 403


def test_write_blocked_during_curfew(client, alif_token):
    with patch("app.middleware.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 4, 4, 22, 30, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        resp = client.post(
            "/rules",
            json={"title": "Test Rule", "description": "Test"},
            headers=auth_header(alif_token),
        )
        assert resp.status_code == 403
        assert "curfew" in resp.json()["detail"].lower()


def test_write_allowed_with_emergency_override(client, alif_token):
    with patch("app.middleware.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 4, 4, 23, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        resp = client.post(
            "/rules",
            json={"title": "Emergency", "description": "Urgent", "emergency_override": True},
            headers=auth_header(alif_token),
        )
        assert resp.status_code != 403


def test_get_allowed_during_curfew(client, alif_token):
    with patch("app.middleware.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 4, 4, 23, 0, 0)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        resp = client.get("/rules", headers=auth_header(alif_token))
        assert resp.status_code != 403
