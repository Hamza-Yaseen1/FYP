import hashlib
import hmac
import json
import os

import pytest

TEST_SECRET = "test_app_secret"
os.environ["WHATSAPP_APP_SECRET"] = TEST_SECRET
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "1308658958991189")


@pytest.fixture
def _fake_ai(monkeypatch):
    async def fake_analyze(content, message_id=None, user_id=None):
        return {
            "priority": "normal",
            "confidence": 0.0,
            "explanation": "stubbed",
            "summary": "stubbed summary",
            "recommended_action": "",
            "recommended_actions": [],
            "tasks_extracted": [],
            "deadlines": [],
            "provider": "stub",
            "analyzed_at": None,
            "status": "completed",
        }

    monkeypatch.setattr("services.webhook_ingest.analyze_message", fake_analyze)


def _signature(body: bytes, secret: str = TEST_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _meta_object_payload(
    messages=None,
    field="messages",
    phone_number_id=PHONE_NUMBER_ID,
):
    """Build a Meta webhook POST body in the format Meta actually sends."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "2588143401638348",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "+1 555 660-8724",
                                "phone_number_id": phone_number_id,
                            },
                            "contacts": [
                                {"wa_id": "12345", "profile": {"name": "Ali"}}
                            ],
                            "messages": messages,
                        },
                        "field": field,
                    }
                ],
            }
        ],
    }


def _text_message(message="Send me the slides tonight.", message_id="wamid.TEST1"):
    return {
        "from": "12345",
        "id": message_id,
        "timestamp": "1700000000",
        "type": "text",
        "text": {"body": message},
    }


# ── US2: Incoming Deliveries Are Verified Before Processing ──────────


def test_post_rejects_invalid_signature(client):
    body = json.dumps(_meta_object_payload(messages=[_text_message()])).encode()
    wrong = "sha256=" + hmac.new(
        b"wrong_app_secret", body, hashlib.sha256
    ).hexdigest()
    res = client.post(
        "/webhooks/whatsapp",
        content=body,
        headers={"X-Hub-Signature-256": wrong},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "Invalid signature"


def test_post_rejects_missing_signature(client):
    body = json.dumps(_meta_object_payload(messages=[_text_message()])).encode()
    res = client.post("/webhooks/whatsapp", content=body)
    assert res.status_code == 403
    assert res.json()["detail"] == "Invalid signature"


def test_post_rejects_empty_secret_configuration(client):
    previous = os.environ.get("WHATSAPP_APP_SECRET")
    os.environ["WHATSAPP_APP_SECRET"] = ""
    try:
        body = json.dumps(
            _meta_object_payload(messages=[_text_message()])
        ).encode()
        res = client.post(
            "/webhooks/whatsapp",
            content=body,
            headers={"X-Hub-Signature-256": _signature(body)},
        )
        assert res.status_code == 403
    finally:
        if previous is None:
            del os.environ["WHATSAPP_APP_SECRET"]
        else:
            os.environ["WHATSAPP_APP_SECRET"] = previous


def test_verification_challenge_echoes_challenge(client):
    res = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "my_fyp_secret_123",
            "hub.challenge": "1234567890",
        },
    )
    assert res.status_code == 200
    assert res.text == "1234567890"


def test_verification_challenge_wrong_token_403(client):
    res = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "1234567890",
        },
    )
    assert res.status_code == 403


# ── US1: Real WhatsApp Message Reaches the Dashboard ────────────────


def _register_with_whatsapp(client, email):
    res = client.post(
        "/auth/register",
        json={"name": "Ali", "email": email, "password": "s3cretpass"},
    )
    assert res.status_code == 201
    uid = res.json()["id"]
    res = client.post("/connections", json={"provider": "whatsapp"})
    assert res.status_code == 201
    return uid


def _signed_post(client, payload_dict):
    body = json.dumps(payload_dict).encode()
    return client.post(
        "/webhooks/whatsapp",
        content=body,
        headers={"X-Hub-Signature-256": _signature(body)},
    )


def test_post_ingests_real_text_message(client, sync_db, _fake_ai):
    uid = _register_with_whatsapp(client, "webhook-a@example.com")
    res = _signed_post(
        client, _meta_object_payload(messages=[_text_message()])
    )
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

    doc = sync_db.messages.find_one(
        {"external_message_id": "wamid.TEST1"}
    )
    assert doc is not None
    assert doc["source"] == "whatsapp"
    assert doc["sender"] == "Ali"
    assert doc["content"] == "Send me the slides tonight."
    assert doc["message_type"] == "text"
    assert doc["user_id"] == uid
    assert doc["received_at"] is not None
    assert doc["status"] == "unread"


def test_media_only_message_stored(client, sync_db, _fake_ai):
    _register_with_whatsapp(client, "webhook-media@example.com")
    media = {
        "from": "12345",
        "id": "wamid.MEDIA1",
        "timestamp": "1700000000",
        "type": "image",
        "image": {"id": "media-id-1"},
    }
    res = _signed_post(client, _meta_object_payload(messages=[media]))
    assert res.status_code == 200

    doc = sync_db.messages.find_one({"external_message_id": "wamid.MEDIA1"})
    assert doc is not None
    assert doc["content"] == ""
    assert doc["message_type"] == "media"
    assert doc["sender"] == "Ali"


def test_post_batched_multiple_messages(client, sync_db, _fake_ai):
    _register_with_whatsapp(client, "webhook-batch@example.com")
    res = _signed_post(
        client,
        _meta_object_payload(
            messages=[
                _text_message(message="First batch message", message_id="wamid.B1"),
                _text_message(message="Second batch message", message_id="wamid.B2"),
            ]
        ),
    )
    assert res.status_code == 200
    assert sync_db.messages.count_documents(
        {"external_message_id": {"$in": ["wamid.B1", "wamid.B2"]}}
    ) == 2


def test_post_non_message_event_ignored(client, sync_db, _fake_ai):
    _register_with_whatsapp(client, "webhook-status@example.com")
    res = _signed_post(client, _meta_object_payload(messages=None, field="statuses"))
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    assert sync_db.messages.count_documents({}) == 0


# ── US3: Normalized Format and Simulation Parity ────────────────────


def _simulate_post(client, sender="Alice", message="Send me the slides tonight."):
    return client.post(
        "/webhooks/simulate", json={"sender": sender, "message": message}
    )


def test_simulate_endpoint_ingests_with_source(client, sync_db, _fake_ai):
    res = client.post(
        "/auth/register",
        json={"name": "Sim User", "email": "webhook-sim@example.com", "password": "s3cretpass"},
    )
    assert res.status_code == 201
    uid = res.json()["id"]

    res = _simulate_post(client)
    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "simulate"
    assert data["sender"] == "Alice"
    assert data["content"] == "Send me the slides tonight."

    doc = sync_db.messages.find_one({"user_id": uid, "source": "simulate"})
    assert doc is not None
    assert doc["message_type"] == "text"


def test_simulate_requires_auth(client):
    client.cookies.clear()
    assert _simulate_post(client).status_code == 401


def test_simulate_and_real_identical_analysis(client, sync_db, _fake_ai):
    _register_with_whatsapp(client, "webhook-parity@example.com")
    text = "Send me the slides tonight."

    sim_res = _simulate_post(client, message=text)
    assert sim_res.status_code == 200

    real_res = _signed_post(
        client,
        _meta_object_payload(
            messages=[_text_message(message=text, message_id="wamid.PARITY1")]
        ),
    )
    assert real_res.status_code == 200

    sim_doc = sync_db.messages.find_one({"source": "simulate", "content": text})
    real_doc = sync_db.messages.find_one({"source": "whatsapp", "content": text})
    assert sim_doc is not None
    assert real_doc is not None

    sim_ai = sim_doc.get("ai_analysis") or {}
    real_ai = real_doc.get("ai_analysis") or {}
    assert sim_ai["priority"] == real_ai["priority"]
    assert sim_ai["summary"] == real_ai["summary"]


# ── US4: Duplicate Deliveries Collapse to One Document ──────────────


def test_post_duplicate_external_id_single_document(client, sync_db, _fake_ai):
    _register_with_whatsapp(client, "webhook-dup@example.com")
    payload = _meta_object_payload(
        messages=[_text_message(message_id="wamid.DUP1")]
    )

    first = _signed_post(client, payload)
    assert first.status_code == 200
    assert first.json() == {"status": "ok"}

    second = _signed_post(client, payload)
    assert second.status_code == 200
    assert second.json() == {"status": "ok"}

    assert sync_db.messages.count_documents({"external_message_id": "wamid.DUP1"}) == 1


def test_duplicate_does_not_reanalyze(client, sync_db, monkeypatch):
    calls = []

    async def fake_analyze(content, message_id=None, user_id=None):
        calls.append(message_id)
        return {
            "priority": "normal",
            "confidence": 0.0,
            "explanation": "stubbed",
            "summary": "stubbed summary",
            "recommended_action": "",
            "recommended_actions": [],
            "tasks_extracted": [],
            "deadlines": [],
            "provider": "stub",
            "analyzed_at": None,
            "status": "completed",
        }

    monkeypatch.setattr("services.webhook_ingest.analyze_message", fake_analyze)

    _register_with_whatsapp(client, "webhook-dup2@example.com")
    payload = _meta_object_payload(
        messages=[_text_message(message_id="wamid.DUP2")]
    )
    _signed_post(client, payload)
    _signed_post(client, payload)

    assert len(calls) == 1


# ── US5: Server-Side Ownership and Filtering ───────────────────────


def test_post_without_connected_connection_acknowledged(client, sync_db, _fake_ai):
    res = _signed_post(client, _meta_object_payload(messages=[_text_message()]))
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    assert sync_db.messages.count_documents({}) == 0


def test_post_unknown_phone_number_ignored(client, sync_db, _fake_ai):
    _register_with_whatsapp(client, "webhook-phn@example.com")
    payload = _meta_object_payload(
        messages=[_text_message(message_id="wamid.PHN1")],
        phone_number_id="999000999",
    )
    res = _signed_post(client, payload)
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    assert sync_db.messages.count_documents({}) == 0