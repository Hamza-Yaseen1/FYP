# API Contract Changes: Complete AI Pipeline

**Feature**: 006-complete-ai-pipeline | **Date**: 2026-08-21

No new endpoints. No breaking changes — two additive response fields.

## Modified: `GET /messages`, `GET /messages/{id}`, `POST /messages`, `POST /webhooks/whatsapp`

All message responses now include the attention fields inside
`ai_analysis`:

```json
{
  "id": "68a...",
  "sender": "Ali",
  "content": "Please send the FYP slides tonight.",
  "source": "whatsapp",
  "status": "unread",
  "state": "active",
  "ai_analysis": {
    "priority": "urgent",
    "confidence": 0.92,
    "explanation": "...",
    "summary": "Slides must be sent tonight.",
    "recommended_action": "Send the slides before tonight.",
    "recommended_actions": ["Send the slides before tonight."],
    "tasks_extracted": [
      {
        "description": "Send FYP slides",
        "deadline": "Tonight",
        "priority_indicator": null,
        "requires_action": true
      }
    ],
    "deadlines": ["Tonight"],
    "needs_attention": true,
    "attention_reason": "A task with a near deadline was detected.",
    "provider": "groq",
    "analyzed_at": "2026-08-21T14:03:11Z",
    "status": "completed"
  },
  "created_at": "2026-08-21T14:02:58Z",
  "updated_at": "2026-08-21T14:03:12Z"
}
```

### Field contract

| Field | Type | Invariant |
|-------|------|-----------|
| `ai_analysis.needs_attention` | boolean | `true` only when R1 (task ∧ near-term deadline) or R2 (urgent ∧ task) holds |
| `ai_analysis.attention_reason` | string | Non-empty iff `needs_attention` is true; one of the two fixed reason strings |

Legacy messages analyzed before this feature return
`needs_attention: false, attention_reason: ""` via model defaults.

## Unchanged

- `PUT /messages/{id}`, `DELETE /messages/{id}`, `/tasks/*`, `/health`
- Request payloads for all endpoints (no input changes)
- Status codes and error shapes

## Frontend consumption rules

- Dashboard and Attention pages read these fields from stored responses;
  they MUST NOT recompute flag state client-side.
- Attention page filters `GET /messages` results on
  `ai_analysis.needs_attention === true`.
