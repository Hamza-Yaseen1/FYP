# Data Model: Normalized Inbound Message + Dedup Index

**Feature**: 014-whatsapp-webhook | **Date**: 2026-08-28 | **Phase**: 1

## 1. Scope

Day 23 adds webhook ingestion to the existing `messages` collection
(see `specs/013-whatsapp-business/data-model.md` for the established shape).
Two fields are added and one optional field is added to the API response. No
collection is renamed or restructured; legacy and simulate documents remain
valid.

## 2. Stored Message Document (MongoDB `messages`)

```json
{
  "_id": "ObjectId(...)",
  "user_id": "string (user UUID this message belongs to)",

  "source": "'whatsapp' | 'simulate' | 'web' (existing values)",
  "sender": "string — for whatsapp: profile.name, else messages[].from (wa_id)",
  "content": "string — text.body for text; empty string for media",
  "message_type": "'text' | 'media'  (NEW; default 'text')",

  "external_message_id": "string — Meta message.id e.g. 'wamid.HBgz...' (NEW, optional)",
  "received_at": "datetime UTC — server ingestion time (NEW, optional)",

  "status": "'unread' (initial), updated by the app",
  "state": "'active' (initial), 'archived'/'deleted' via app",
  "created_at": "datetime UTC — set equal to received_at on ingest",
  "updated_at": "datetime UTC",

  "ai_analysis": {
    "priority": "'pending' initially",
    "...": "set by the AI pipeline (see models/message.py AIAnalysis)"
  }
}
```

### Field notes

- `external_message_id` is **optional at the document level**: simulate, web,
  and legacy documents do not carry it, so no migration of existing rows.
- `received_at` is server UTC at insertion. Client/Provider timestamps are
  **never trusted** (Meta's `messages[].timestamp` is not used for ownership
  or ordering).
- `message_type="text"` when Meta's `type == "text"`, else `"media"`. A media
  message keeps `content=""` and `sender` set so the dashboard can render a
  media-marked card (spec FR-007 / SC-006). Media files are NOT downloaded.
- `created_at` equals `received_at` for webhook messages (assigned inside
  `ingest_message`).

## 3. Indexes

```python
await messages_collection.create_index(
    [("external_message_id", 1)],
    unique=True,
    partialFilterExpression={"external_message_id": {"$type": "string"}},
)
```

Created in `main.py` lifespan (alongside the existing `user_id`/`created_at`
indexes). Properties:

- **Unique** → the database, not application logic, guarantees that the same
  Meta `wamid` is stored at most once, even under concurrent redeliveries.
- **Partial** → documents without `external_message_id` (simulate, web,
  legacy) are exempted, so uniqueness loosening is scoped.
- On violation, the ingest service catches the `DuplicateKeyError`, fetches
  the existing document id, and acknowledges — no re-analysis (spec SC-003).

## 4. Response Surface (API only, not stored)

`MessageResponse` (`backend/models/message.py`) gains two optional fields so
the dashboard can show dedup/source metadata without breaking simulate/legacy
messages:

- `external_message_id?: str`
- `received_at?: datetime`

`message_doc_to_response` emits them only when present. Existing fields
(`id`, `sender`, `content`, `source`, `status`, `state`, `ai_analysis`,
`created_at`, `updated_at`) are unchanged.

## 5. Hard Requirements

- Partial filter must use `$type: "string"`, NOT `$exists: true` — the
  `$exists` variant would make a future explicit `null` a unique-key failure.
- The dedup index must exist BEFORE the real webhook is exercised; create it
  in the same lifespan that ensures the user/content indexes.
- Simulate ingests (`source="simulate"`) do NOT set `external_message_id`,
  keeping the simulation path exempt from dedup (its content-based guard was
  only on the old webhook route).