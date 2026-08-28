# Feature Specification: WhatsApp Business Integration Research + Setup

**Feature Branch**: `013-whatsapp-business`  
**Created**: 2026-08-26  
**Status**: Draft  
**Input**: User description: "Create a clear and focused specification for Day 22 – WhatsApp Business Integration Research + Setup"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Meta Developer Account & App Setup (Priority: P1)

As a developer setting up the Communication AI system, I need to create a
Meta Developer account and register a WhatsApp Business App so that the
system can send and receive messages through the official WhatsApp Business
Platform Cloud API.

**Why this priority**: Without a registered Meta Developer app and WhatsApp
Business product, no webhook can be configured and no messages can be
received. This is the foundation for all WhatsApp integration work.

**Independent Test**: Can be fully tested by verifying the Meta Developer
portal shows the app with WhatsApp product added, a test phone number
associated, and credentials (Phone Number ID, Access Token) available for
use.

**Acceptance Scenarios**:

1. **Given** a developer with a Meta/Facebook account, **When** they create
   a Meta Developer account and register a new app, **Then** the app appears
   in the Meta Developer dashboard with a valid App ID.
2. **Given** the registered app, **When** the WhatsApp Business product is
   added, **Then** a WhatsApp Business Account (WABA) and a test phone
   number are associated with the app.
3. **Given** the WhatsApp Business product is active, **When** the developer
   navigates to the API Setup section, **Then** a Phone Number ID and a
   temporary Access Token are displayed and can be copied.

---

### User Story 2 - Public Webhook Endpoint Setup (Priority: P1)

As a developer, I need to expose the backend webhook endpoint publicly
using ngrok so that Meta's servers can deliver incoming WhatsApp messages
to our system during development.

**Why this priority**: Meta requires a publicly accessible HTTPS URL for
webhook delivery. Without this, webhook verification and message reception
cannot happen.

**Independent Test**: Can be fully tested by running ngrok, confirming the
tunnel is active, and verifying the public URL resolves to the backend
webhook endpoint over HTTPS.

**Acceptance Scenarios**:

1. **Given** the backend server running locally, **When** ngrok is started
   pointing to the backend port, **Then** a public HTTPS URL is generated
   (e.g., `https://xxxx.ngrok-free.app`).
2. **Given** the ngrok URL, **When** a GET request is made to the webhook
   path, **Then** the backend responds with the expected verification
   challenge response.

---

### User Story 3 - Webhook Configuration & Verification (Priority: P1)

As a developer, I need to configure the webhook URL in the Meta Developer
portal and complete the verification challenge so that Meta confirms our
endpoint is valid and begins sending incoming message events.

**Why this priority**: Webhook verification is the gateway to receiving
real WhatsApp messages. Until Meta confirms the endpoint, no messages
will be delivered.

**Independent Test**: Can be fully tested by checking the Meta Developer
portal shows the webhook as "Verified" and a test message sent to the
Business number is received by the endpoint.

**Acceptance Scenarios**:

1. **Given** a running ngrok tunnel and a configured webhook URL in Meta,
   **When** the developer clicks "Verify and Save" in the portal, **Then**
   Meta sends a verification challenge and the portal shows the webhook as
   verified.
2. **Given** a verified webhook, **When** a test message is sent to the
   WhatsApp Business number, **Then** the backend receives the webhook
   payload and logs the incoming message.

---

### User Story 4 - Credential Security & Environment Setup (Priority: P2)

As a developer, I need all WhatsApp Business credentials stored securely
in environment variables so that sensitive data is never exposed in code,
version control, or logs.

**Why this priority**: Security is non-negotiable. Credentials in code or
logs create vulnerabilities. This must be set up correctly from the start.

**Independent Test**: Can be fully tested by confirming all credentials
appear in `.env.local` only, `.env.local` is gitignored, and no hardcoded
secrets exist in the codebase.

**Acceptance Scenarios**:

1. **Given** WhatsApp Business credentials obtained from Meta, **When** the
   developer stores them in `.env.local`, **Then** the application can
   read them at runtime without exposing them in responses or logs.
2. **Given** credentials in `.env.local`, **When** `git status` is
   checked, **Then** `.env.local` is not listed as a tracked or staged
   file.

---

### User Story 5 - Official Message Flow Understanding (Priority: P2)

As a developer, I need to understand the official WhatsApp Business Cloud
API message flow so that the implementation on Day 23 follows the correct
architecture and handles all edge cases properly.

**Why this priority**: Understanding the message flow prevents
architectural mistakes during implementation. This is research, not code.

**Independent Test**: Can be tested by reviewing documented notes on the
message flow and confirming they cover: inbound webhook structure, message
types, delivery acknowledgments, and error handling.

**Acceptance Scenarios**:

1. **Given** the Meta WhatsApp Business documentation, **When** the
   developer studies the message flow, **Then** they can explain: how a
   message moves from a user's phone to the webhook, what the webhook
   payload contains, and how to acknowledge receipt.
2. **Given** understanding of the message flow, **When** planning Day 23
   implementation, **Then** the developer can identify which fields from
   the webhook payload map to the existing message schema.

---

### Edge Cases

- What happens when the ngrok tunnel expires or disconnects during
  testing? The webhook becomes unreachable; Meta will retry delivery
  for a limited period, then mark messages as undelivered.
- What happens if the Meta Access Token expires? The temporary token
  from the API Setup page is short-lived; for production, a System User
  Token or long-lived token is needed (Day 23 concern, not Day 22).
- What happens if the webhook verification fails? Meta will not send
  any messages; the portal shows the webhook as unverified. Common
  causes: wrong URL, wrong verify token, backend not responding over
  HTTPS.
- What happens if the test phone number has no remaining free messages?
  Meta provides a limited number of free test messages per month; once
  exhausted, a paid WhatsApp Business Account is required.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Developer MUST be able to create a Meta Developer account
  using an existing Facebook/Meta account.
- **FR-002**: Developer MUST be able to register a new app in the Meta
  Developer portal and add the WhatsApp Business product.
- **FR-003**: System MUST support receiving incoming webhook verification
  challenges (GET request with `hub.mode`, `hub.verify_token`,
  `hub.challenge`) from Meta.
- **FR-004**: System MUST validate incoming webhook requests using Meta's
  `X-Hub-Signature-256` HMAC signature before processing.
- **FR-005**: System MUST store all WhatsApp Business credentials
  (Phone Number ID, WhatsApp Business Account ID, Access Token, Webhook
  Verify Token) in environment variables only.
- **FR-006**: System MUST serve the webhook endpoint over HTTPS (via ngrok
  tunnel during development).
- **FR-007**: Developer MUST be able to verify the webhook in the Meta
  Developer portal and receive confirmation of successful verification.
- **FR-008**: System MUST log incoming webhook payloads for debugging
  during the research phase (without exposing credentials).
- **FR-009**: Developer MUST document the official WhatsApp Business Cloud
  API message flow for reference during Day 23 implementation.
- **FR-010**: System MUST NOT attempt to read, access, or process personal
  WhatsApp notifications or messages from personal accounts.

### Key Entities

- **WhatsApp Business App**: A registered application in the Meta Developer
  portal that enables WhatsApp Business Platform API access. Key
  attributes: App ID, App Secret, WhatsApp Business Account ID.
- **Webhook Configuration**: The endpoint URL and verification token
  registered in Meta to receive incoming message events. Key attributes:
  callback URL, verify token, subscription fields.
- **Environment Credentials**: Sensitive values stored in `.env.local`
  for backend use. Includes: `WHATSAPP_PHONE_NUMBER_ID`,
  `WHATSAPP_BUSINESS_ACCOUNT_ID`, `WHATSAPP_ACCESS_TOKEN`,
  `WHATSAPP_VERIFY_TOKEN`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Meta Developer account is created and a WhatsApp Business App
  is registered with the WhatsApp product added, verified within 15 minutes.
- **SC-002**: A test phone number is associated with the WhatsApp Business
  Account and a Phone Number ID is obtainable from the API Setup page.
- **SC-003**: ngrok tunnel is active and the backend webhook endpoint is
  accessible over HTTPS from a public URL.
- **SC-004**: Webhook verification completes successfully in the Meta
  Developer portal (portal shows "Verified" status).
- **SC-005**: A test message sent to the WhatsApp Business number is
  received by the backend webhook endpoint within 30 seconds.
- **SC-006**: All four WhatsApp Business credentials are stored in
  `.env.local` with zero hardcoded secrets in the codebase.
- **SC-007**: Developer has documented notes on the official message flow
  covering: inbound payload structure, message types, acknowledgment
  mechanism, and error responses.

## Assumptions

- The developer has an existing Facebook/Meta account that can be used to
  create a Meta Developer account.
- ngrok is installed and available for creating a public HTTPS tunnel to
  the local backend server.
- The backend server can be configured to serve a webhook verification
  endpoint at a known path (e.g., `/webhook/whatsapp`).
- Day 22 is research and setup only; full message reception, storage, and
  AI pipeline integration are deferred to Day 23.
- The Meta Developer free tier provides enough test messages for Day 22
  verification (typically 1,000 free test messages per month).
- The temporary Access Token from the API Setup page is sufficient for
  Day 22 testing; long-lived token generation is a Day 23 concern.

## Out of Scope (Day 23+)

The following items are explicitly deferred and NOT part of Day 22:

- Full message reception, parsing, and storage in MongoDB
- Integration with the AI pipeline (priority, summary, task extraction)
- Processing different message types (text, image, audio, document)
- Sending outbound messages (auto-reply, template messages, broadcasts)
- Long-lived Access Token or System User Token setup
- Production deployment (removing ngrok dependency)
- Multi-user WhatsApp connection support
- Webhook payload decryption for encrypted messages
