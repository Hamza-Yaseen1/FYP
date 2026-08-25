# API Contracts: Day 18 – User Isolation

**Date**: 2026-08-25
**Feature**: 009-user-isolation

## Changes Summary

No new endpoints are introduced. All existing endpoints already enforce
`user_id` filtering. The contracts below document the expected behavior
for isolation verification.

## POST /messages (unchanged)

**Request**: `{ "sender": str, "content": str, "source": str }`
**Response 201**: Message object with `user_id` set to the authenticated
user's ID.
**Isolation**: The `user_id` is set server-side from the JWT — never from
the request body.

## GET /messages (unchanged)

**Response 200**: Array of message objects where `user_id` matches the
authenticated user. Sorted by `created_at` descending. Limit 100.
**Isolation**: Query filters on `{"user_id": uid}`. No cross-user data
is returned.

## GET /messages/{id} (unchanged)

**Response 200**: Single message object if it belongs to the authenticated
user.
**Response 404**: If the message does not exist OR belongs to another user.
The response body is identical in both cases.

## PUT /messages/{id} (unchanged)

**Response 200**: Updated message object if it belongs to the
authenticated user.
**Response 404**: If the message does not exist OR belongs to another user.

## DELETE /messages/{id} (unchanged)

**Response 204**: If the message belongs to the authenticated user and is
deleted.
**Response 404**: If the message does not exist OR belongs to another user.

## PUT /messages/{id}/priority (unchanged)

**Response 200**: Updated message object if it belongs to the
authenticated user.
**Response 404**: If the message does not exist OR belongs to another user.

## GET /tasks (unchanged)

**Response 200**: Array of task objects where `user_id` matches the
authenticated user. Sorted by `created_at` descending. Limit 100.
**Isolation**: Query filters on `{"user_id": uid}`. No cross-user data
is returned.

## PUT /tasks/{id}/status (unchanged)

**Response 200**: Updated task object if it belongs to the authenticated
user.
**Response 404**: If the task does not exist OR belongs to another user.

## DELETE /tasks/{id} (unchanged)

**Response 204**: If the task belongs to the authenticated user and is
deleted.
**Response 404**: If the task does not exist OR belongs to another user.

## POST /webhooks/whatsapp (unchanged)

**Response 200**: Webhook result with the created/updated message.
**Isolation**: The `user_id` is set from the authenticated user's JWT
session. Webhook messages are scoped to the authenticating user.

## POST /auth/login (unchanged)

**Response 200**: User object + `cai_token` cookie set.
**Isolation**: No change. Login establishes the session used for all
subsequent isolation checks.

## POST /auth/logout (unchanged)

**Response 200**: `{ "ok": true }` + `cai_token` cookie cleared.
**Isolation**: Clears the session cookie. Frontend must clear all
client-side state on logout.
