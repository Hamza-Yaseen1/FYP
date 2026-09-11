# Contracts: Cross-Platform Dashboard

**Phase 1 output** — **no new endpoints**. The dashboard is a read-only
consumer of one existing, authenticated, user-scoped endpoint. The
contract is documented below for implementers; it is not changed by this
feature.

## `GET /messages` — List my messages (EXISTING, consumed)

- **Auth**: required. Identity + `user_id` scoping come server-side from
  the verified session cookie (`get_current_user`). All queries start with
  `{"user_id": <uid>}`.
- **Query params**: optional; the dashboard calls with **no params** (tab
  defaults to `all`, limit defaults to 100). Params `tab`, `source`,
  `priority`, `sender`, `start_date`, `end_date`, `search`, `limit`,
  `offset` exist for the Inbox and remain unchanged.
- **Method**: `GET http://localhost:8000/messages`
- **Response 200**:

```json
{
  "messages": [
    {
      "id": "64f...",
      "sender": "Ali",
      "content": "Send the slides tonight.",
      "source": "whatsapp",
      "subject": null,
      "status": "unread",
      "state": "active",
      "created_at": "2026-09-11T09:41:00Z",
      "ai_analysis": {
        "priority": "urgent",
        "confidence": 0.92,
        "summary": "Ali needs the FYP slides before tonight.",
        "recommended_action": "Send the slides before tonight.",
        "tasks_extracted": [
          { "description": "Send FYP slides", "deadline": "Tonight",
            "priority_indicator": "urgent", "requires_action": true }
        ],
        "deadlines": ["Tonight"],
        "needs_attention": true,
        "attention_reason": "A task with a near deadline was detected."
      }
    }
  ],
  "total": 42,
  "limit": 100,
  "offset": 0
}
```

- **Wait/Fallback**: `GET /messages` may include `ai_analysis.status =
  "pending"` or `"skipped"` and a `priority: "pending"` — the dashboard
  handles these by moving the message to the Pending tail group.
- **Error contract**: `401` unauthenticated (frontend `apiFetch` redirects
  to `/login`); `404` resources of other users are never returned (user
  scoping).

### Dashboard derivation (client-side, from the payload above)

1. Group by `ai_analysis.priority` → URGENT / IMPORTANT / NORMAL / LOW /
   Pending (missing or `pending` analysis → Pending).
2. Sort each group by `created_at` desc (stable).
3. Hide empty groups; render group headers + cards.

### Cross-checks

- No new OpenAPI additions; `backend/openapi.json` (if exported) is
  unchanged.
- `GET /messages/counts` exists but is **not required** by this feature
  (group section counts can be `[].length` of the fetched payload).