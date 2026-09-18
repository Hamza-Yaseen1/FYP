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

REGISTER_A = {"name": "User A", "email": "sec-a@test.com", "password": "passA12345"}
REGISTER_B = {"name": "User B", "email": "sec-b@test.com", "password": "passB12345"}


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


async def _stub_ai_with_task(content, message_id=None, user_id=None, thread_id=None):
    return {
        "priority": "important",
        "confidence": 0.9,
        "explanation": "stubbed",
        "summary": "stubbed summary",
        "recommended_action": "Review document",
        "recommended_actions": ["Review document"],
        "tasks_extracted": [
            {"description": "Review the quarterly report", "deadline": "Friday"}
        ],
        "deadlines": ["Friday"],
        "provider": "stub",
        "analyzed_at": datetime.now(timezone.utc),
        "status": "completed",
    }


class TestIsolationSecurityMatrix:
    @pytest.fixture(autouse=True)
    def _patch_ai(self, monkeypatch):
        # POST /messages runs analysis in the background via
        # services.webhook_ingest._analyze_and_store, so patch the module
        # that actually calls process_message.
        monkeypatch.setattr("services.webhook_ingest.process_message", _stub_ai)

    def _register(self, client, body):
        res = client.post("/auth/register", json=body)
        assert res.status_code == 201
        return res.json()["id"], res.cookies.get("cai_token")

    def _switch(self, client, token):
        client.cookies.clear()
        if token:
            client.cookies.set("cai_token", token)

    def _connect_whatsapp(self, client):
        res = client.post("/connections", json={"provider": "whatsapp"})
        assert res.status_code == 201
        return res.json()["id"]

    def _signed_webhook(self, client, payload):
        body = json.dumps(payload).encode()
        sig = hmac.new(TEST_SECRET.encode(), body, hashlib.sha256).hexdigest()
        return client.post(
            "/webhooks/whatsapp",
            content=body,
            headers={"X-Hub-Signature-256": f"sha256={sig}"},
        )

    def _meta_payload(self, message, wamid="wamid.SEC",
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
                                    {"wa_id": "99999", "profile": {"name": "Sec Contact"}}
                                ],
                                "messages": [
                                    {
                                        "from": "99999",
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

    # ── T004: B cannot delete A's connection → 404 (same as non-existent) ───

    def test_user_b_delete_returns_404_for_a_connection(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        conn_a_id = self._connect_whatsapp(client)

        uid_b, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)

        res_b = client.delete(f"/connections/{conn_a_id}")
        assert res_b.status_code == 404

        fake_id = str(ObjectId())
        res_fake = client.delete(f"/connections/{fake_id}")
        assert res_fake.status_code == 404

    # ── T005: B's connection list excludes A's connections ───────────────────

    def test_user_b_connection_list_excludes_a(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        self._connect_whatsapp(client)

        uid_b, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        self._connect_whatsapp(client)

        self._switch(client, tok_a)
        res_a = client.get("/connections")
        conn_ids_a = [c["id"] for c in res_a.json()["connections"]]
        assert len(conn_ids_a) == 1

        self._switch(client, tok_b)
        res_b = client.get("/connections")
        conn_ids_b = [c["id"] for c in res_b.json()["connections"]]
        assert len(conn_ids_b) == 1
        assert conn_ids_a[0] != conn_ids_b[0]

    # ── T006: A's connection list excludes B's ──────────────────────────────

    def test_user_a_connections_list_excludes_b(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        conn_a_id = self._connect_whatsapp(client)

        uid_b, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        self._connect_whatsapp(client)

        self._switch(client, tok_a)
        res = client.get("/connections")
        assert res.status_code == 200
        conn_ids = [c["id"] for c in res.json()["connections"]]
        assert conn_a_id in conn_ids
        assert len(conn_ids) == 1

    # ── T007: Analytics user isolation ──────────────────────────────────────

    def test_analytics_user_isolation(self, client, sync_db, monkeypatch):
        monkeypatch.setattr(
            "services.webhook_ingest.process_message", _stub_ai_with_task
        )

        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)

        for i in range(3):
            client.post(
                "/webhooks/simulate",
                json={"sender": "A Contact", "message": f"A message {i}"},
            )

        uid_b, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)

        for i in range(5):
            client.post(
                "/webhooks/simulate",
                json={"sender": "B Contact", "message": f"B message {i}"},
            )

        self._switch(client, tok_a)
        analytics_a = client.get("/analytics?period=week").json()
        assert analytics_a["total"] == 3

        self._switch(client, tok_b)
        analytics_b = client.get("/analytics?period=week").json()
        assert analytics_b["total"] == 5

    # ── Guessed message ObjectId → 404 ─────────────────────────────────────

    def test_cross_user_guessed_message_id_returns_404(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        res = client.post(
            "/messages",
            json={"sender": "Test", "content": "A secret", "source": "simulated"},
        )
        msg_a_id = res.json()["id"]

        uid_b, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)

        res_direct = client.get(f"/messages/{msg_a_id}")
        assert res_direct.status_code == 404

        guessed = str(ObjectId())
        res_guessed = client.get(f"/messages/{guessed}")
        assert res_guessed.status_code == 404

        assert res_direct.json() == res_guessed.json()
