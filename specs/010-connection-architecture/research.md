# Research: Connection Architecture

**Date**: 2026-08-25
**Feature**: 010-connection-architecture
**Phase**: 0 - Research

## Research Questions

### 1. Token Encryption Approach

**Question**: How should access tokens and refresh tokens be encrypted at rest?

**Decision**: Use AES-256-CBC encryption via Python's `cryptography` library.

**Rationale**:
- AES-256 is industry standard for data encryption at rest
- CBC mode provides good security with proper IV handling
- `cryptography` is well-maintained and widely used
- Simple to implement with minimal code

**Alternatives Considered**:
- **RSA encryption**: Asymmetric, but tokens are small and we control both encrypt/decrypt. AES is simpler.
- **Fernet symmetric encryption**: Built on AES but adds complexity. Raw AES-256 is sufficient.
- **Database field-level encryption**: MongoDB has some support but adds complexity. Application-level is simpler.

**Implementation Notes**:
- Encryption key stored in `ENCRYPTION_KEY` environment variable
- Generate key with `Fernet.generate_key()` or use 32-byte hex string
- Use random IV for each encryption operation
- Store IV alongside ciphertext (prepend or separate field)

### 2. OAuth Flow Implementation

**Question**: How should OAuth flows be implemented for WhatsApp and Gmail?

**Decision**: Use simple redirect-based OAuth 2.0 flow with backend handling.

**Rationale**:
- Standard OAuth 2.0 authorization code flow
- Backend handles token exchange and storage
- Frontend only initiates redirect and receives callback
- Tokens never touch frontend code

**Alternatives Considered**:
- **Client-side OAuth**: Tokens would be exposed to frontend. Violates security rules.
- **Third-party OAuth library**: Adds dependency. Manual implementation is simple enough for FYP.
- **Mock OAuth for prototype**: Could work but doesn't demonstrate real security.

**Implementation Notes**:
- Backend initiates OAuth redirect with state parameter
- Callback endpoint receives authorization code
- Backend exchanges code for tokens
- Tokens encrypted and stored in database
- For FYP: Mock OAuth flow with simulated tokens for demo

### 3. Connection Status Management

**Question**: How should connection status be computed and managed?

**Decision**: Status is computed server-side based on token validity and provider availability.

**Rationale**:
- Status should reflect actual connection health
- Frontend only displays status, never computes it
- Server can check token expiry and provider API health
- Status values: `connected`, `disconnected`, `error`, `coming_soon`

**Alternatives Considered**:
- **Client-computed status**: Would require exposing token info to frontend. Violates security.
- **Static status**: Doesn't reflect real connection health. Not useful.
- **Webhook-based status**: Adds complexity. Not needed for foundation.

**Implementation Notes**:
- On connection creation: status = `connected`
- On token refresh failure: status = `error`
- On explicit disconnect: status = `disconnected`
- For unsupported providers: status = `coming_soon`
- Status checked on each API request (lightweight check)

### 4. User Isolation Enforcement

**Question**: How should user isolation be enforced for connections?

**Decision**: Every database query must filter by `user_id` as first condition.

**Rationale**:
- Follows existing User Isolation Rules from constitution
- Prevents any cross-user data leakage
- Simple to implement and verify
- Consistent with messages and tasks isolation

**Alternatives Considered**:
- **Application-level filtering**: Could miss edge cases. Database-level is safer.
- **Row-level security**: MongoDB doesn't have native RLS. Application-level is required.
- **Separate collections per user**: Adds complexity. Single collection with filtering is simpler.

**Implementation Notes**:
- Extract `user_id` from verified JWT session
- Every query includes `{"user_id": user_id}` as first filter
- Delete operations also filter by `user_id`
- API responses never include `user_id` field (implicit ownership)

### 5. API Response DTO Design

**Question**: How should API responses be designed to exclude sensitive fields?

**Decision**: Use Pydantic response models that explicitly exclude token fields.

**Rationale**:
- Pydantic models control serialization
- Explicit exclusion prevents accidental exposure
- Type-safe and easy to verify
- Consistent with existing API patterns

**Alternatives Considered**:
- **Manual dict filtering**: Error-prone, could miss fields.
- **Query projection**: Database-level exclusion, but application-level is safer.
- **Serialization middleware**: Adds complexity. Explicit models are simpler.

**Implementation Notes**:
- `ConnectionResponse` model includes: id, provider, status, createdAt
- `ConnectionResponse` excludes: user_id, accessToken, refreshToken
- All API endpoints use `ConnectionResponse` for output
- Never return raw database documents

## Technology Choices

### Backend
- **FastAPI**: Already in use, async support, good for API development
- **Motor**: Async MongoDB driver, already in use
- **Pydantic**: Data validation, already in use
- **cryptography**: AES-256 encryption, well-maintained

### Frontend
- **Next.js 16.3**: Already in use, App Router
- **TypeScript**: Type safety, already in use
- **Tailwind CSS**: Styling, already in use
- **shadcn/ui**: Components, already in use

## Risk Assessment

### Low Risk
- Database schema design (straightforward)
- Frontend UI components (standard patterns)
- API endpoint creation (standard REST)

### Medium Risk
- Token encryption implementation (must be correct)
- OAuth flow integration (external dependency)
- User isolation enforcement (must be thorough)

### Mitigation Strategies
- **Token encryption**: Use well-tested library, write unit tests
- **OAuth flow**: Mock for FYP, document real implementation
- **User isolation**: Automated testing with two users

## Assumptions Validated

1. **OAuth flows available**: Assumed configured in system. For FYP, mock implementation acceptable.
2. **Users have provider accounts**: Assumed for demo purposes.
3. **Connection status computed server-side**: Validated as correct approach.
4. **"Coming Soon" providers static**: Validated, no backend needed for LinkedIn.
