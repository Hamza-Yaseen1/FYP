from datetime import datetime, timezone

import pytest
from bson import ObjectId


REGISTER_A = {"name": "User A", "email": "isolation-a@test.com", "password": "passA12345"}
REGISTER_B = {"name": "User B", "email": "isolation-b@test.com", "password": "passB12345"}

TASK_CONTENT = "Please review the quarterly report and send feedback by Friday"


async def _fake_analyze(message_content, message_id=None, user_id=None):
    tasks = []
    if "review" in message_content.lower():
        tasks.append({
            "description": "Review the quarterly report",
            "deadline": "Friday",
            "priority_indicator": "high",
        })
    return {
        "priority": "important",
        "confidence": 0.95,
        "explanation": "stubbed",
        "summary": "stubbed summary",
        "recommended_action": "Review document",
        "recommended_actions": ["Review document"],
        "tasks_extracted": tasks,
        "deadlines": ["Friday"],
        "provider": "stub",
        "analyzed_at": datetime.now(timezone.utc),
        "status": "completed",
    }


class TestUserIsolation:
    @pytest.fixture(autouse=True)
    def _patch_analyzer(self, monkeypatch):
        monkeypatch.setattr("routes.messages.analyze_message", _fake_analyze)
        monkeypatch.setattr("routes.webhooks.analyze_message", _fake_analyze)

    def _register(self, client, body):
        res = client.post("/auth/register", json=body)
        assert res.status_code == 201
        return res.json()["id"], res.cookies.get("cai_token")

    def _switch(self, client, token):
        client.cookies.clear()
        if token:
            client.cookies.set("cai_token", token)

    def _msg_body(self, content, source="simulated"):
        return {"sender": "Test Contact", "content": content, "source": source}

    def _create_task(self, sync_db, user_id, description="Test task", status="pending"):
        now = datetime.now(timezone.utc)
        result = sync_db.tasks.insert_one({
            "user_id": user_id,
            "description": description,
            "deadline": None,
            "priority_indicator": None,
            "requires_action": True,
            "status": status,
            "source_message_id": str(ObjectId()),
            "source_message_preview": description[:80],
            "created_at": now,
        })
        return str(result.inserted_id)

    # ── US1: Messages Are Private ──────────────────────────────────

    def test_user_a_messages_visible_only_to_a(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        res = client.post("/messages", json=self._msg_body("A private message"))
        assert res.status_code == 201
        msg_a_id = res.json()["id"]

        _, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)

        listing = client.get("/messages")
        assert listing.status_code == 200
        assert all(m["id"] != msg_a_id for m in listing.json())

    def test_user_b_messages_visible_only_to_b(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        res_a = client.post("/messages", json=self._msg_body("A message"))
        msg_a_id = res_a.json()["id"]

        _, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        res = client.post("/messages", json=self._msg_body("B private message"))
        assert res.status_code == 201
        msg_b_id = res.json()["id"]

        listing = client.get("/messages")
        assert listing.status_code == 200
        msg_ids = [m["id"] for m in listing.json()]
        assert msg_b_id in msg_ids
        assert msg_a_id not in msg_ids

    def test_cross_user_get_message_returns_404(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        res = client.post("/messages", json=self._msg_body("A secret"))
        msg_a_id = res.json()["id"]

        _, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        assert client.get(f"/messages/{msg_a_id}").status_code == 404

    def test_cross_user_update_message_returns_404(self, client, sync_db):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        res = client.post("/messages", json=self._msg_body("A update test"))
        msg_a_id = res.json()["id"]

        _, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        assert client.put(f"/messages/{msg_a_id}", json={"status": "read"}).status_code == 404

        doc = sync_db.messages.find_one({"_id": ObjectId(msg_a_id)})
        assert doc["status"] == "unread"

    def test_cross_user_delete_message_returns_404(self, client, sync_db):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        res = client.post("/messages", json=self._msg_body("A delete test"))
        msg_a_id = res.json()["id"]

        _, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        assert client.delete(f"/messages/{msg_a_id}").status_code == 404

        doc = sync_db.messages.find_one({"_id": ObjectId(msg_a_id)})
        assert doc is not None

    def test_cross_user_priority_override_returns_404(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        res = client.post("/messages", json=self._msg_body("A priority test"))
        msg_a_id = res.json()["id"]

        _, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        assert client.put(f"/messages/{msg_a_id}/priority?priority=urgent").status_code == 404

    def test_owner_can_access_own_message(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        res = client.post("/messages", json=self._msg_body("A own access"))
        msg_a_id = res.json()["id"]

        assert client.get(f"/messages/{msg_a_id}").status_code == 200

    # ── US2: Tasks Are Private ─────────────────────────────────────

    def test_tasks_created_with_user_id(self, client, sync_db):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        client.post("/messages", json=self._msg_body(TASK_CONTENT))

        msg = sync_db.messages.find_one({"user_id": uid_a})
        assert msg is not None
        assert msg["ai_analysis"]["tasks_extracted"]

    def test_user_a_tasks_visible_only_to_a(self, client, sync_db):
        uid_a, tok_a = self._register(client, REGISTER_A)
        task_a_id = self._create_task(sync_db, uid_a, "A private task")

        uid_b, tok_b = self._register(client, REGISTER_B)
        task_b_id = self._create_task(sync_db, uid_b, "B private task")

        self._switch(client, tok_a)
        listing_a = client.get("/tasks").json()
        task_ids_a = [t["id"] for t in listing_a]

        self._switch(client, tok_b)
        listing_b = client.get("/tasks").json()
        task_ids_b = [t["id"] for t in listing_b]

        assert task_a_id in task_ids_a
        assert task_a_id not in task_ids_b
        assert task_b_id in task_ids_b
        assert task_b_id not in task_ids_a

    def test_cross_user_update_task_returns_404(self, client, sync_db):
        uid_a, tok_a = self._register(client, REGISTER_A)
        task_id = self._create_task(sync_db, uid_a, "A task")

        _, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        assert client.put(f"/tasks/{task_id}/status", json={"status": "completed"}).status_code == 404

        task_doc = sync_db.tasks.find_one({"_id": ObjectId(task_id)})
        assert task_doc["status"] == "pending"

    def test_cross_user_delete_task_returns_404(self, client, sync_db):
        uid_a, tok_a = self._register(client, REGISTER_A)
        task_id = self._create_task(sync_db, uid_a, "A task")

        _, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        assert client.delete(f"/tasks/{task_id}").status_code == 404

        assert sync_db.tasks.find_one({"_id": ObjectId(task_id)}) is not None

    def test_all_tasks_have_user_id(self, client, sync_db):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._create_task(sync_db, uid_a, "A task")

        uid_b, tok_b = self._register(client, REGISTER_B)
        self._create_task(sync_db, uid_b, "B task")

        all_tasks = list(sync_db.tasks.find({}))
        assert len(all_tasks) >= 2
        for task in all_tasks:
            assert "user_id" in task
            assert task["user_id"] in [uid_a, uid_b]

    # ── US3: AI Analysis Stays With Owner ──────────────────────────

    def test_ai_analysis_not_leaked_via_cross_user_messages(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        client.post("/messages", json=self._msg_body(TASK_CONTENT))

        _, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        listing = client.get("/messages").json()
        assert len(listing) == 0

    def test_ai_analysis_not_leaked_via_cross_user_message_detail(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        res = client.post("/messages", json=self._msg_body(TASK_CONTENT))
        msg_a_id = res.json()["id"]

        _, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        assert client.get(f"/messages/{msg_a_id}").status_code == 404

    def test_message_doc_has_ai_analysis(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        res = client.post("/messages", json=self._msg_body(TASK_CONTENT))
        msg = res.json()
        assert msg.get("ai_analysis") is not None
        assert msg["ai_analysis"]["priority"] == "important"

    # ── US4: Webhook Messages Are Scoped to Owner ──────────────────

    def test_webhook_message_scoped_to_authenticating_user(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        webhook_res = client.post(
            "/webhooks/whatsapp",
            json={"sender": "Alice", "message": TASK_CONTENT, "timestamp": "2026-08-25T10:00:00Z"},
        )
        assert webhook_res.status_code == 200

        _, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        listing = client.get("/messages").json()
        assert len(listing) == 0

        self._switch(client, tok_a)
        listing_a = client.get("/messages").json()
        assert len(listing_a) >= 1

    def test_webhook_tasks_scoped_to_authenticating_user(self, client, sync_db):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        client.post(
            "/webhooks/whatsapp",
            json={"sender": "Alice", "message": TASK_CONTENT, "timestamp": "2026-08-25T11:00:00Z"},
        )

        uid_b, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        tasks_b = client.get("/tasks").json()
        assert len(tasks_b) == 0

        self._switch(client, tok_a)
        tasks_a = client.get("/tasks").json()
        assert len(tasks_a) == 0

        msg = sync_db.messages.find_one({"user_id": uid_a, "source": "whatsapp"})
        assert msg is not None

    # ── US5: Dashboard Shows Only My Data ──────────────────────────

    def test_dashboard_data_isolation(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        client.post("/messages", json=self._msg_body("A dashboard msg"))

        uid_b, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        client.post("/messages", json=self._msg_body("B dashboard msg"))

        self._switch(client, tok_a)
        msgs_a = client.get("/messages").json()

        self._switch(client, tok_b)
        msgs_b = client.get("/messages").json()

        ids_a = {m["id"] for m in msgs_a}
        ids_b = {m["id"] for m in msgs_b}
        assert len(ids_a & ids_b) == 0
        assert len(ids_a) == 1
        assert len(ids_b) == 1

    # ── US6: Logout Clears Cross-User State ────────────────────────

    def test_logout_clears_session(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        client.post("/messages", json=self._msg_body("A logout test"))

        res = client.post("/auth/logout")
        assert res.status_code == 204

        client.cookies.clear()
        assert client.get("/messages").status_code == 401
        assert client.get("/tasks").status_code == 401

    def test_new_user_sees_no_stale_data(self, client):
        uid_a, tok_a = self._register(client, REGISTER_A)
        self._switch(client, tok_a)
        client.post("/messages", json=self._msg_body("A stale data"))

        client.post("/auth/logout")
        client.cookies.clear()

        uid_b, tok_b = self._register(client, REGISTER_B)
        self._switch(client, tok_b)
        msgs = client.get("/messages").json()
        assert len(msgs) == 0
        tasks = client.get("/tasks").json()
        assert len(tasks) == 0
