# Research: Cross-Platform Dashboard

**Phase 0 output** — resolves the technical unknowns from the plan's
Technical Context. Feature branch `018-cross-platform-dashboard`, dated
2026-09-11.

## 1. Where should the priority grouping happen?

**Unknown**: The spec requires messages grouped by priority, but the
backend has no grouped endpoint today (`GET /messages/counts` returns
counts only; `GET /messages` returns a flat list, default sort
`created_at` desc, limit 100).

**Decision**: Group client-side in the frontend, reusing the existing
`GET /messages` endpoint. No new backend endpoint.

**Rationale**:
- **Simplicity First (Principle I)**: the simplest viable implementation
  that meets the spec is a fetch + group in the UI. The response already
  carries the full `Message` + `ai_analysis` shape — everything a card
  needs is in one call.
- **Existing precedent**: `MessageList` (`components/MessageList.tsx:45`)
  already implements a `priorityOrder` map (`urgent 0 → important 1 →
  normal 2 → low 3 → pending 4`) and sorts priorities + recency
  client-side. `NeedsAttentionSection` also filters client-side. Adding a
  backend bucket endpoint would duplicate this logic and add contract,
  test, and maintenance surface for zero user-visible gain at FYP scale
  (≤ 200 messages).
- **Constitution Day 27**: "Dashboard renders from stored MongoDB data
  only — it formats, it does not compute" — formatting/grouping stored
  values is exactly what client-side grouping does; no AI or
  re-classification is involved.

**Alternatives considered**:
- A new `GET /dashboard` grouped endpoint on the backend — rejected: more
  moving parts, needs its own tests/contract, and yields no benefit below
  dataset sizes where a single 100-message fetch is trivial.
- Grouping server-side on `GET /messages` via a param — rejected: changes
  an existing multi-consumer endpoint (Inbox) for one consumer.

**Risk**: none material. If message volume ever exceeds ~200, the
dashboard can add a dedicated endpoint later without breaking clients
(reversible decision, Decision Guideline 4).

## 2. Which priority groups and how are they ordered?

**Unknown**: The spec says "Urgent → Important → Normal → Low"; the
stored `ai_analysis.priority` enum is `urgent | important | normal | low
| pending`.

**Decision**: Render four priority groups in the fixed order URGENT,
IMPORTANT, NORMAL, LOW, plus a **Pending analysis** tail group for
messages whose `ai_analysis.priority` is `pending` (or missing). Within a
group, order by `created_at` descending (newest first).

**Rationale**:
- The four-group order matches both the user requirement and the priority
  ordering already used by `MessageList` and the Inbox.
- A separate Pending tail (rather than forcing unanalyzed messages into
  NORMAL) satisfies the spec's requirement that pending messages "MUST NOT
  collide with classified groups"; it reads clearly and keeps classified
  groups accurate.
- Empty groups are hidden entirely (spec FR-007 / constitution Day 27) —
  a user with nothing urgent never sees an "URGENT" header.

**Alternatives considered**:
- Merge `pending` into NORMAL with an indicator — rejected: it inflates
  the NORMAL group and hides the fact that analysis hasn't run.
- Skip `pending` messages entirely — rejected: violates Progressive
  Enhancement (Principle VII) and the spec's pending-handling edge case.

## 3. What does a card show and where does each value come from?

**Unknown**: exact per-card source-of-truth mapping.

**Decision**: Every field on `PlatformMessageCard` maps directly to stored
data (`Message` / `ai_analysis`), matching the constitution's "fidelity"
rule — no recombination:

| Card field | Source (stored) | Fallback |
|---|---|---|
| Priority | `ai_analysis.priority` | Pending badge |
| Main title | `ai_analysis.tasks_extracted[0].description` | `ai_analysis.summary` → `content` preview |
| Source • Sender | `source` enum + `sender` | readable fallback label |
| Time | `created_at` (via `useTimeAgo`) | "just now" |
| Deadline | `tasks_extracted[0].deadline` (original wording) | omit |
| Subject | `subject` (Gmail only) | omit |
| Recommended action | `ai_analysis.recommended_action` | omit |
| Needs attention | `ai_analysis.needs_attention` + `attention_reason` | omit |

**Rationale**: mirrors the title logic already used by
`NeedsAttentionCard` (task desc → summary → content) and the "Why it
matters" display, keeping one mental model across the app. `useTimeAgo`
already formats created_at as "2h ago".

**Alternatives considered**: re-deriving a title from raw `content` always
— rejected: task/summary carry more triage value and match the attention
cards.

## 4. How are source labels rendered?

**Unknown**: icon + label treatment for sources.

**Decision**: reuse the existing pill treatment (`rounded-full border px-2
py-0.5 text-[10px] ... uppercase`) used by `MessageList` for the source
(`whatsapp` / `gmail`), plus a lucide icon (`MessageCircle` for WhatsApp,
`Mail` for Gmail). Unknown/future sources render a neutral pill with the
raw `source` string and a generic icon.

**Rationale**: consistent with the current design system (same pill, same
uppercase micro-label tokens as `MessageList.tsx:170`); no new visual
vocabulary. The label is informational only — it never affects grouping.

## 5. Any backend or data-model changes?

**Decision**: None. The `messages` collection and all message routes are
unchanged. The dashboard is a pure consumer.

**Rationale**: the `Message` / `ai_analysis` document already contains
every field the cards need (`source`, `sender`, `content`, `subject`,
`created_at`, `priority`, `summary`, `tasks_extracted[].description`,
`deadlines`, `recommended_action`, `needs_attention`, `attention_reason`).
`GET /messages` is user-scoped (routes/messages.py base query `{"user_id":
uid}`), so user isolation holds automatically.

**Alternatives considered**: adding a "low" bucket anywhere in the backend
— rejected, `low` already exists in the data model.

## Consolidated decisions

| Unknown | Decision | Rationale |
|---|---|---|
| Grouping location | Frontend client-side via existing `GET /messages` | Simplicity First; existing precedent; ≤200 msgs |
| Group order | URGENT → IMPORTANT → NORMAL → LOW → Pending | Spec + existing `priorityOrder` |
| Within-group order | `created_at` desc (newest first) | Spec + Inbox default |
| Pending messages | Tail "Pending analysis" group | Spec; keeps classified groups accurate |
| Card fields | All from stored `Message`/`ai_analysis` | Constitution fidelity rule |
| Source label | Existing pill + source icon; friendly fallback | Design consistency |
| Backend changes | None | Everything needed already exists & is user-scoped |