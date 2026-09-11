import hashlib
import hmac
import json
import os
from datetime import datetime, timezone

import pytest
from bson import ObjectId

TEST_SECRET = "test_app_secret"
os.environ["WHATSAPP_APP_SECRET"] = TEST_SECRET
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "1308658958991189")


async def _stub_ai(content, message_id=None, user_id=None, thread_id=None):
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


def _register(client, email):
    res = client.post(
        "/auth/register",
        json={"name": "Dedup User", "email": email, "password": "s3cretpass"},
    )
    assert res.status_code == 201
    return res.json()["id"], res.cookies.get("cai_token")


def _switch(client, token):
    client.cookies.clear()
    if token:
        client.cookies.set("cai_token", token)


def _connect_whatsapp(client):
    res = client.post("/connections", json={"provider": "whatsapp"})
    assert res.status_code == 201
    return res.json()["id"]


def _signature(body: bytes, secret: str = TEST_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _meta_payload(message, wamid="wamid.DEDUP",
                  phone_number_id=PHONE_NUMBER_ID):
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "2588143401638348",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "+1 555 000-0001",
                                "phone_number_id": phone_number_id,
                            },
                            "contacts": [
                                {"wa_id": "11111", "profile": {"name": "Dedup Contact"}}
                            ],
                            "messages": [
                                {
                                    "from": "11111",
                                    "id": wamid,
                                    "timestamp": "1700000000",
                                    "type": "text",
                                    "text": {"body": message},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def _signed_post(client, payload_dict):
    body = json.dumps(payload_dict).encode()
    return client.post(
        "/webhooks/whatsapp",
        content=body,
        headers={"X-Hub-Signature-256": _signature(body)},
    )


class TestDedupe:
    @pytest.fixture(autouse=True)
    def _patch_ai(self, monkeypatch):
        monkeypatch.setattr("services.webhook_ingest.process_message", _stub_ai)

    # ── T022: Same external_message_id twice → 1 document ─────────────────

    def test_same_external_id_twice_yields_one_document(self, client, sync_db):
        uid, tok = _register(client, "dedup-one@test.com")
        _switch(client, tok)
        _connect_whatsapp(client)

        payload = _meta_payload("Dedup test", wamid="wamid.DEDUP1")
        first = _signed_post(client, payload)
        assert first.status_code == 200

        second = _signed_post(client, payload)
        assert second.status_code == 200

        count = sync_db.messages.count_documents(
            {"external_message_id": "wamid.DEDUP1"}
        )
        assert count == 1

    # ── T023: Duplicate skips reanalysis ────────────────────────────────────

    def test_duplicate_skips_reanalysis(self, client, sync_db, monkeypatch):
        calls = []

        async def tracking_analyze(content, message_id=None, user_id=None, thread_id=None):
            calls.append(message_id)
            return {
                "priority": "normal",
                "confidence": 0.0,
                "explanation": "stubbed",
                "summary": "stubbed",
                "recommended_action": "",
                "recommended_actions": [],
                "tasks_extracted": [],
                "deadlines": [],
                "provider": "stub",
                "analyzed_at": None,
                "status": "completed",
            }

        monkeypatch.setattr("services.webhook_ingest.process_message", tracking_analyze)

        uid, tok = _register(client, "dedup-rean@test.com")
        _switch(client, tok)
        _connect_whatsapp(client)

        payload = _meta_payload("Reanalysis test", wamid="wamid.DEDUP2")
        _signed_post(client, payload)
        _signed_post(client, payload)

        assert len(calls) == 1

    # ── T024: Cross-user same external_id → 2 independent documents (RED) ─
    # Uses direct DB insert for user B because _resolve_owner() always
    # returns the first connected WhatsApp user (documented single-WABA limitation).

    def test_cross_user_same_external_id_independent(self, client, sync_db):
        now = datetime.now(timezone.utc)

        uid_a, tok_a = _register(client, "dedup-cross-a@test.com")
        _switch(client, tok_a)
        _connect_whatsapp(client)

        payload_a = _meta_payload("A shared message", wamid="wamid.SHARED1")
        res_a = _signed_post(client, payload_a)
        assert res_a.status_code == 200

        uid_b, tok_b = _register(client, "dedup-cross-b@test.com")
        doc_b = {
            "_id": ObjectId(),
            "user_id": uid_b,
            "source": "whatsapp",
            "sender": "Cross User",
            "content": "B shared message",
            "message_type": "text",
            "status": "unread",
            "state": "active",
            "created_at": now,
            "updated_at": now,
            "received_at": now,
            "external_message_id": "wamid.SHARED1",
        }
        sync_db.messages.insert_one(doc_b)

        docs_a = list(
            sync_db.messages.find(
                {"user_id": uid_a, "external_message_id": "wamid.SHARED1"}
            )
        )
        docs_b = list(
            sync_db.messages.find(
                {"user_id": uid_b, "external_message_id": "wamid.SHARED1"}
            )
        )
        assert len(docs_a) == 1
        assert len(docs_b) == 1
        assert docs_a[0]["user_id"] == uid_a
        assert docs_b[0]["user_id"] == uid_b

        total = sync_db.messages.count_documents(
            {"external_message_id": "wamid.SHARED1"}
        )
        assert total == 2

    # ── T025: Key-less simulate → 2 documents per delivery ─────────────────

    def test_keyless_simulate_stored_once_per_delivery(self, client, sync_db):
        uid, tok = _register(client, "dedup-keyless@test.com")
        _switch(client, tok)

        client.post(
            "/webhooks/simulate",
            json={"sender": "Alice", "message": "Keyless dedup test"},
        )
        client.post(
            "/webhooks/simulate",
            json={"sender": "Alice", "message": "Keyless dedup test"},
        )

        count = sync_db.messages.count_documents(
            {"user_id": uid, "source": "simulate"}
        )
        assert count == 2
