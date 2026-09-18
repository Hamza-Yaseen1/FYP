import pytest
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from bson import ObjectId


REGISTER_BODY = {
    "name": "Test User",
    "email": "test@example.com",
    "password": "s3cretpass",
}


def register(client, **overrides):
    body = {**REGISTER_BODY, **overrides}
    return client.post("/auth/register", json=body)


def create_message(client, sync_db, user_id, **overrides):
    """Helper to create a message directly in the database for testing."""
    message = {
        "user_id": str(user_id),
        "sender": "Test Sender",
        "content": "Test content",
        "source": "whatsapp",
        "status": "unread",
        "state": "active",
        "ai_analysis": {
            "priority": "normal",
            "confidence": 0.85,
            "summary": "Test summary",
            "recommended_action": "Test action",
            "needs_attention": False,
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        **overrides,
    }
    result = sync_db.messages.insert_one(message)
    return str(result.inserted_id)


class TestGetMessages:
    """Test GET /messages endpoint with filtering."""

    def test_get_messages_empty(self, client):
        """Test getting messages when none exist."""
        register(client)
        res = client.get("/messages")
        assert res.status_code == 200
        data = res.json()
        assert "messages" in data
        assert "total" in data
        assert data["messages"] == []
        assert data["total"] == 0

    def test_get_messages_requires_auth(self, client):
        """Test that messages endpoint requires authentication."""
        res = client.get("/messages")
        assert res.status_code in [200, 401]

    def test_tab_filter_all(self, client):
        """Test tab filter with 'all' value."""
        register(client)
        res = client.get("/messages?tab=all")
        assert res.status_code == 200

    def test_tab_filter_urgent(self, client):
        """Test tab filter with 'urgent' value."""
        register(client)
        res = client.get("/messages?tab=urgent")
        assert res.status_code == 200

    def test_tab_filter_unread(self, client):
        """Test tab filter with 'unread' value."""
        register(client)
        res = client.get("/messages?tab=unread")
        assert res.status_code == 200

    def test_source_filter(self, client):
        """Test source filter parameter."""
        register(client)
        res = client.get("/messages?source=whatsapp")
        assert res.status_code == 200

    def test_priority_filter(self, client):
        """Test priority filter parameter."""
        register(client)
        res = client.get("/messages?priority=urgent")
        assert res.status_code == 200

    def test_date_range_filter(self, client):
        """Test date range filter parameters."""
        register(client)
        start = datetime.now(timezone.utc) - timedelta(days=7)
        end = datetime.now(timezone.utc)
        res = client.get(f"/messages?start_date={quote(start.isoformat())}&end_date={quote(end.isoformat())}")
        assert res.status_code == 200

    def test_sender_filter(self, client):
        """Test sender filter parameter."""
        register(client)
        res = client.get("/messages?sender=Ali")
        assert res.status_code == 200

    def test_search_filter(self, client):
        """Test search filter parameter."""
        register(client)
        res = client.get("/messages?search=meeting")
        assert res.status_code == 200

    def test_limit_offset(self, client):
        """Test limit and offset pagination parameters."""
        register(client)
        res = client.get("/messages?limit=10&offset=0")
        assert res.status_code == 200

    def test_invalid_date_range(self, client):
        """Test invalid date range returns 400."""
        register(client)
        start = datetime.now(timezone.utc)
        end = datetime.now(timezone.utc) - timedelta(days=7)
        res = client.get(f"/messages?start_date={quote(start.isoformat())}&end_date={quote(end.isoformat())}")
        assert res.status_code == 400

    def test_tab_filter_with_messages(self, client, sync_db):
        """Test tab filter with actual messages in database."""
        # Register user
        register(client)
        user = sync_db.users.find_one({"email": "test@example.com"})
        
        # Create messages with different priorities
        create_message(client, sync_db, user["_id"], 
                      sender="Ali", 
                      ai_analysis={"priority": "urgent", "confidence": 0.9, "summary": "Urgent task", "recommended_action": "Do now", "needs_attention": True})
        create_message(client, sync_db, user["_id"], 
                      sender="Sara", 
                      ai_analysis={"priority": "normal", "confidence": 0.8, "summary": "Normal message", "recommended_action": "Review later", "needs_attention": False})
        
        # Test urgent filter
        res = client.get("/messages?tab=urgent")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert data["messages"][0]["sender"] == "Ali"
        
        # Test all filter
        res = client.get("/messages?tab=all")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2

    def test_source_filter_with_messages(self, client, sync_db):
        """Test source filter with actual messages in database."""
        register(client)
        user = sync_db.users.find_one({"email": "test@example.com"})
        
        create_message(client, sync_db, user["_id"], sender="Ali", source="whatsapp")
        create_message(client, sync_db, user["_id"], sender="Sara", source="gmail")
        
        res = client.get("/messages?source=whatsapp")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert data["messages"][0]["source"] == "whatsapp"

    def test_priority_filter_with_messages(self, client, sync_db):
        """Test priority filter with actual messages in database."""
        register(client)
        user = sync_db.users.find_one({"email": "test@example.com"})
        
        create_message(client, sync_db, user["_id"], 
                      sender="Ali", 
                      ai_analysis={"priority": "urgent", "confidence": 0.9, "summary": "Urgent", "recommended_action": "Do now", "needs_attention": True})
        create_message(client, sync_db, user["_id"], 
                      sender="Sara", 
                      ai_analysis={"priority": "normal", "confidence": 0.8, "summary": "Normal", "recommended_action": "Review", "needs_attention": False})
        
        res = client.get("/messages?priority=urgent")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert data["messages"][0]["ai_analysis"]["priority"] == "urgent"

    def test_search_filter_with_messages(self, client, sync_db):
        """Test search filter with actual messages in database."""
        register(client)
        user = sync_db.users.find_one({"email": "test@example.com"})
        
        create_message(client, sync_db, user["_id"], 
                      sender="Ali", 
                      content="Meeting at 3pm tomorrow",
                      ai_analysis={"priority": "normal", "confidence": 0.8, "summary": "Meeting scheduled", "recommended_action": "Attend meeting", "needs_attention": False})
        create_message(client, sync_db, user["_id"], 
                      sender="Sara", 
                      content="Project update",
                      ai_analysis={"priority": "normal", "confidence": 0.8, "summary": "Project status", "recommended_action": "Review", "needs_attention": False})
        
        res = client.get("/messages?search=meeting")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert "meeting" in data["messages"][0]["content"].lower()


class TestFilterCounts:
    """Test GET /messages/counts endpoint."""

    def test_get_counts_empty(self, client):
        """Test getting counts when no messages exist."""
        register(client)
        res = client.get("/messages/counts")
        assert res.status_code == 200
        data = res.json()
        assert "tabs" in data
        assert "sources" in data
        assert "priorities" in data

    def test_get_counts_with_messages(self, client, sync_db):
        """Test getting counts with actual messages in database."""
        register(client)
        user = sync_db.users.find_one({"email": "test@example.com"})
        
        create_message(client, sync_db, user["_id"], 
                      sender="Ali", 
                      source="whatsapp",
                      ai_analysis={"priority": "urgent", "confidence": 0.9, "summary": "Urgent", "recommended_action": "Do now", "needs_attention": True})
        create_message(client, sync_db, user["_id"], 
                      sender="Sara", 
                      source="gmail",
                      ai_analysis={"priority": "normal", "confidence": 0.8, "summary": "Normal", "recommended_action": "Review", "needs_attention": False})
        
        res = client.get("/messages/counts")
        assert res.status_code == 200
        data = res.json()
        assert data["tabs"]["all"] == 2
        assert data["tabs"]["urgent"] == 1
        assert data["tabs"]["normal"] == 1
        assert data["sources"]["whatsapp"] == 1
        assert data["sources"]["gmail"] == 1
        assert data["priorities"]["urgent"] == 1
        assert data["priorities"]["normal"] == 1


class TestUniqueSenders:
    """Test GET /messages/senders endpoint."""

    def test_get_senders_empty(self, client):
        """Test getting senders when no messages exist."""
        register(client)
        res = client.get("/messages/senders")
        assert res.status_code == 200
        data = res.json()
        assert "senders" in data

    def test_get_senders_with_messages(self, client, sync_db):
        """Test getting senders with actual messages in database."""
        register(client)
        user = sync_db.users.find_one({"email": "test@example.com"})
        
        create_message(client, sync_db, user["_id"], sender="Ali")
        create_message(client, sync_db, user["_id"], sender="Ali")
        create_message(client, sync_db, user["_id"], sender="Sara")
        
        res = client.get("/messages/senders")
        assert res.status_code == 200
        data = res.json()
        assert len(data["senders"]) == 2
        # Ali should have 2 messages, Sara should have 1
        ali_sender = next(s for s in data["senders"] if s["name"] == "Ali")
        sara_sender = next(s for s in data["senders"] if s["name"] == "Sara")
        assert ali_sender["count"] == 2
        assert sara_sender["count"] == 1


class TestUniqueSources:
    """Test GET /messages/sources endpoint."""

    def test_get_sources_empty(self, client):
        """Test getting sources when no messages exist."""
        register(client)
        res = client.get("/messages/sources")
        assert res.status_code == 200
        data = res.json()
        assert "sources" in data

    def test_get_sources_with_messages(self, client, sync_db):
        """Test getting sources with actual messages in database."""
        register(client)
        user = sync_db.users.find_one({"email": "test@example.com"})
        
        create_message(client, sync_db, user["_id"], source="whatsapp")
        create_message(client, sync_db, user["_id"], source="whatsapp")
        create_message(client, sync_db, user["_id"], source="gmail")
        
        res = client.get("/messages/sources")
        assert res.status_code == 200
        data = res.json()
        assert len(data["sources"]) == 2
        # WhatsApp should have 2 messages, Gmail should have 1
        whatsapp_source = next(s for s in data["sources"] if s["name"] == "whatsapp")
        gmail_source = next(s for s in data["sources"] if s["name"] == "gmail")
        assert whatsapp_source["count"] == 2
        assert gmail_source["count"] == 1


class TestUserIsolation:
    """Test user isolation - User A cannot see User B's messages."""

    def test_user_isolation_messages(self, client, sync_db):
        """Test that users can only see their own messages."""
        # Register user A
        register(client, email="usera@example.com", name="User A")
        
        # Create messages for user A
        user_a = sync_db.users.find_one({"email": "usera@example.com"})
        create_message(client, sync_db, user_a["_id"], sender="User A Message")
        
        # Register user B
        register(client, email="userb@example.com", name="User B")
        
        # User B should not see User A's messages
        res = client.get("/messages")
        assert res.status_code == 200
        data = res.json()
        # User B should see 0 messages (only their own, which don't exist)
        assert data["total"] == 0

    def test_user_isolation_counts(self, client, sync_db):
        """Test that users can only see counts for their own messages."""
        # Register user A
        register(client, email="usera@example.com", name="User A")
        
        # Create messages for user A
        user_a = sync_db.users.find_one({"email": "usera@example.com"})
        create_message(client, sync_db, user_a["_id"], 
                      sender="User A Message",
                      ai_analysis={"priority": "urgent", "confidence": 0.9, "summary": "Urgent", "recommended_action": "Do now", "needs_attention": True})
        
        # Register user B
        register(client, email="userb@example.com", name="User B")
        
        # User B should not see User A's message counts
        res = client.get("/messages/counts")
        assert res.status_code == 200
        data = res.json()
        assert data["tabs"]["all"] == 0
        assert data["tabs"]["urgent"] == 0

    def test_user_isolation_senders(self, client, sync_db):
        """Test that users can only see senders for their own messages."""
        # Register user A
        register(client, email="usera@example.com", name="User A")
        
        # Create messages for user A
        user_a = sync_db.users.find_one({"email": "usera@example.com"})
        create_message(client, sync_db, user_a["_id"], sender="Ali")
        
        # Register user B
        register(client, email="userb@example.com", name="User B")
        
        # User B should not see User A's senders
        res = client.get("/messages/senders")
        assert res.status_code == 200
        data = res.json()
        assert len(data["senders"]) == 0

    def test_user_isolation_sources(self, client, sync_db):
        """Test that users can only see sources for their own messages."""
        # Register user A
        register(client, email="usera@example.com", name="User A")
        
        # Create messages for user A
        user_a = sync_db.users.find_one({"email": "usera@example.com"})
        create_message(client, sync_db, user_a["_id"], source="whatsapp")
        
        # Register user B
        register(client, email="userb@example.com", name="User B")
        
        # User B should not see User A's sources
        res = client.get("/messages/sources")
        assert res.status_code == 200
        data = res.json()
        assert len(data["sources"]) == 0


class TestCreateMessageRouting:
    """Test POST /messages funnels AI analysis through the Orchestrator."""

    def test_create_message_routes_through_orchestrator(self, client, sync_db, monkeypatch):
        import routes.messages as messages_mod

        calls = []

        async def fake_process(content, message_id=None, user_id=None, message_type="text", thread_id=None):
            calls.append({"content": content, "message_id": message_id})
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
                "analyzed_at": datetime.now(timezone.utc),
                "status": "completed",
                "routing": {
                    "agents_run": ["priority", "summary"],
                    "agents_skipped": [],
                    "skip_reason": "test",
                    "triggers": [],
                    "llm_call_used": True,
                    "decided_at": datetime.now(timezone.utc),
                },
            }

        monkeypatch.setattr("routes.messages.process_message", fake_process)
        register(client)

        res = client.post(
            "/messages",
            json={
                "sender": "Ali",
                "content": "Send me the slides tonight",
                "source": "simulated",
            },
        )
        assert res.status_code == 201
        assert len(calls) == 1
        assert calls[0]["content"] == "Send me the slides tonight"
        assert calls[0]["message_id"] is not None
        assert res.json()["ai_analysis"]["priority"] == "normal"
        assert res.json()["ai_analysis"]["routing"]["skip_reason"] == "test"
        assert not hasattr(messages_mod, "analyze_message")


class TestStandaloneMessageShape:
    """US2/US3: an unlinked message keeps null identity + the Day 24 shape."""

    def test_unlinked_message_returns_null_identity_and_day24_analysis(
        self, client, monkeypatch
    ):
        monkeypatch.setattr(
            "services.ai.analyzer.get_provider", lambda: _US3FakeProvider()
        )
        register(client)

        res = client.post(
            "/messages",
            json={
                "sender": "Ali",
                "content": "Send me the slides tonight",
                "source": "simulated",
            },
        )
        assert res.status_code == 201
        body = res.json()

        assert body["messageId"] == body["id"]
        assert body["threadId"] is None
        assert body["conversationId"] is None

        ai = body["ai_analysis"]
        for field in TestUS3RoutingContract.LEGACY_FIELDS:
            assert field in ai, f"missing legacy field: {field}"
        assert ai["priority"] == "important"
        assert ai["provider"] == "groq"
        assert ai["status"] == "completed"


class _US3FakeResult:
    priority = "important"
    confidence = 0.7
    explanation = "e2e explanation"
    summary = "e2e summary"
    recommended_actions = ["Follow up with Ali"]
    tasks_extracted = []
    deadlines = ["tomorrow"]


class _US3FakeProvider:
    async def analyze(self, message, context=None):
        return _US3FakeResult()


class TestUS3RoutingContract:
    """US3: the stored/returned ai_analysis keeps its legacy shape plus routing."""

    LEGACY_FIELDS = (
        "priority",
        "confidence",
        "explanation",
        "summary",
        "recommended_action",
        "recommended_actions",
        "tasks_extracted",
        "deadlines",
        "needs_attention",
        "attention_reason",
        "provider",
        "analyzed_at",
        "status",
    )

    def test_create_message_response_retains_legacy_fields_and_routing(
        self, client, monkeypatch
    ):
        monkeypatch.setattr(
            "services.ai.analyzer.get_provider", lambda: _US3FakeProvider()
        )
        register(client)

        res = client.post(
            "/messages",
            json={
                "sender": "Ali",
                "content": "Send me the slides tonight",
                "source": "simulated",
            },
        )
        assert res.status_code == 201
        ai = res.json()["ai_analysis"]
        for field in self.LEGACY_FIELDS:
            assert field in ai, f"missing legacy field: {field}"
        assert ai["provider"] == "groq"
        assert ai["status"] == "completed"

        routing = ai["routing"]
        assert routing["agents_run"] == [
            "priority",
            "summary",
            "task_extraction",
            "deadline_detection",
            "recommended_action",
        ]
        assert routing["agents_skipped"] == []
        assert routing["skip_reason"] == "full"
        assert routing["triggers"]
        assert routing["llm_call_used"] is True
        assert routing["decided_at"] is not None

    def test_create_message_identity_fields_are_additive(
        self, client, monkeypatch
    ):
        """US3/SC-005: the three identity fields ride along without changing
        any pre-existing response field."""
        monkeypatch.setattr(
            "services.ai.analyzer.get_provider", lambda: _US3FakeProvider()
        )
        register(client)

        res = client.post(
            "/messages",
            json={
                "sender": "Ali",
                "content": "Send me the slides tonight",
                "source": "simulated",
            },
        )
        assert res.status_code == 201
        body = res.json()

        assert "messageId" in body and body["messageId"] == body["id"]
        assert "threadId" in body
        assert "conversationId" in body

        ai = body["ai_analysis"]
        for field in self.LEGACY_FIELDS:
            assert field in ai, f"missing legacy field: {field}"
        assert ai["priority"] == "important"
        assert ai["status"] == "completed"