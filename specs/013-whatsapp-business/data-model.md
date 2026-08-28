# Data Model: WhatsApp Business Integration Research + Setup

**Feature**: 013-whatsapp-business
**Date**: 2026-08-26
**Phase**: 1 (Design)

## Overview

Day 22 is research and setup only. The data model below documents the
existing schema that Day 23 will extend to support real WhatsApp
webhook payloads. No new collections or fields are added on Day 22.

## Existing Schema (unchanged on Day 22)

### Messages Collection

The `messages` collection already stores WhatsApp messages from the
fake webhook. Day 23 will update the parsing logic to extract the
same fields from Meta's real payload structure.

| Field | Type | Source | Notes |
|---|---|---|---|
| `_id` | ObjectId | MongoDB auto | Primary key |
| `user_id` | string | Server (JWT) | Owner — set at creation time |
| `sender` | string | Webhook payload | Phone number or contact name |
| `content` | string | Webhook payload | Message text body |
| `source` | string | Hardcoded | Always `"whatsapp"` |
| `status` | string | Server | `"unread"` at creation |
| `state` | string | Server | `"active"` at creation |
| `created_at` | datetime | Webhook payload or server | Message timestamp |
| `updated_at` | datetime | Server | Last update time |
| `ai_analysis` | object | AI pipeline | Priority, summary, tasks, etc. |

### Connections Collection

The `connections` collection stores linked external accounts. Day 23
will create a connection document when the WhatsApp Business account
is linked.

| Field | Type | Source | Notes |
|---|---|---|---|
| `_id` | ObjectId | MongoDB auto | Primary key |
| `user_id` | string | Server (JWT) | Owner |
| `provider` | string | Server | `"whatsapp"` |
| `status` | string | Server | `"connected"`, `"disconnected"`, `"error"` |
| `accessToken` | string | Server (encrypted) | Encrypted WhatsApp access token |
| `refreshToken` | string | Server (encrypted) | Encrypted refresh token (if applicable) |
| `createdAt` | datetime | Server | Connection creation time |

## Day 23 Schema Extensions (planned, not implemented today)

### Webhook Event Log (optional, for debugging)

A temporary collection to log raw webhook events during development.
This helps debug payload parsing issues.

| Field | Type | Source | Notes |
|---|---|---|---|
| `_id` | ObjectId | MongoDB auto | Primary key |
| `user_id` | string | Server (JWT) | Owner |
| `event_type` | string | Parsed | `"message"`, `"status"`, `"verification"` |
| `raw_payload` | object | Webhook | Full Meta webhook payload |
| `received_at` | datetime | Server | When webhook was received |
| `processed` | boolean | Server | Whether payload was successfully parsed |

**Note**: This collection is for development/debugging only and may
be removed before production deployment.

## Entity Relationships

```
User (users collection)
  ├── Messages (messages collection) — one-to-many
  ├── Connections (connections collection) — one-to-many
  └── Tasks (tasks collection) — one-to-many

WhatsApp Business App (external, Meta-managed)
  ├── Phone Number — one-to-many
  └── Webhook — one-to-one per app
```

## Key Mappings: Meta Payload → Existing Schema

| Meta webhook field | Maps to | Notes |
|---|---|---|
| `entry[0].changes[0].value.messages[0].from` | `sender` | Phone number |
| `entry[0].changes[0].value.messages[0].text.body` | `content` | Message text |
| `entry[0].changes[0].value.messages[0].timestamp` | `created_at` | Unix epoch → datetime |
| `entry[0].changes[0].value.messages[0].id` | `message_id` (new) | Meta's unique message ID |
| `entry[0].changes[0].value.contacts[0].profile.name` | `sender_name` (new) | Contact display name |
| hardcoded | `source` | Always `"whatsapp"` |
| server (JWT) | `user_id` | From authenticated session |

## Validation Rules

- `sender` MUST NOT be empty
- `content` MUST NOT be empty (for text messages)
- `source` MUST be `"whatsapp"` for WhatsApp messages
- `user_id` MUST be a valid ObjectId string from the JWT
- `created_at` MUST be a valid datetime
- `message_id` (Day 23) MUST be unique per user for deduplication
