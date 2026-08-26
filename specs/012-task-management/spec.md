# Feature Specification: Task Management

**Feature Branch**: `012-task-management`  
**Created**: 2026-08-26  
**Status**: Draft  
**Input**: User description: "Create a clear and focused specification for Day 21 – Task Management. Create a 'My Tasks' page that shows all extracted tasks clearly with actions: Complete, Snooze, View message."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View My Tasks (Priority: P1)

As a logged-in user, I want to see all my extracted tasks in a clean list so I can understand what needs my attention.

**Why this priority**: This is the core value proposition - without displaying tasks, no other task management actions are possible. This delivers the minimal viable product.

**Independent Test**: Can be fully tested by logging in and verifying the tasks page shows only the current user's tasks with correct priority indicators and deadlines.

**Acceptance Scenarios**:

1. **Given** I am logged in, **When** I navigate to the Tasks page, **Then** I see a list of tasks extracted from my messages.
2. **Given** I am logged in, **When** I view the Tasks page, **Then** each task shows a priority indicator (🔴, 🟡, 🟢), task description, and deadline (if any).
3. **Given** I am logged in, **When** I view the Tasks page, **Then** tasks are sorted with urgent tasks first, followed by important, then normal priority.
4. **Given** I am logged in, **When** I view the Tasks page, **Then** I see only my own tasks - never tasks belonging to other users.
5. **Given** I am logged in, **When** I have no tasks, **Then** I see a clear "No tasks found" message.

---

### User Story 2 - Complete a Task (Priority: P2)

As a logged-in user, I want to mark a task as complete so it moves out of my active task list.

**Why this priority**: Completing tasks is the primary action users take after viewing tasks. This provides closure and helps users track progress.

**Independent Test**: Can be tested by marking a task as complete and verifying it disappears from the active list while remaining in the system.

**Acceptance Scenarios**:

1. **Given** I am viewing my tasks, **When** I click "Complete" on a task, **Then** the task is marked as completed and removed from the active list.
2. **Given** I am viewing my tasks, **When** I click "Complete" on a task, **Then** I see a brief visual confirmation that the task was completed.
3. **Given** I have completed a task, **When** I refresh the page, **Then** the completed task no longer appears in the active list.

---

### User Story 3 - Snooze a Task (Priority: P3)

As a logged-in user, I want to snooze a task to temporarily postpone it so it reappears later.

**Why this priority**: Snoozing provides flexibility for users who want to defer tasks without losing them. This is less critical than viewing and completing tasks.

**Independent Test**: Can be tested by snoozing a task and verifying it disappears temporarily, then reappears after the snooze period.

**Acceptance Scenarios**:

1. **Given** I am viewing my tasks, **When** I click "Snooze" on a task, **Then** I can choose a snooze duration (e.g., 1 hour, tomorrow, next week).
2. **Given** I have snoozed a task, **When** I view my tasks immediately after, **Then** the snoozed task is hidden from the active list.
3. **Given** I have snoozed a task until tomorrow, **When** I view my tasks tomorrow, **Then** the task reappears with the updated deadline.

---

### User Story 4 - View Original Message (Priority: P4)

As a logged-in user, I want to view the original message that created a task so I can understand the context.

**Why this priority**: Context helps users understand why a task was extracted. This is supporting functionality rather than core task management.

**Independent Test**: Can be tested by clicking "View message" and verifying the original message is displayed with sender, source, and content.

**Acceptance Scenarios**:

1. **Given** I am viewing my tasks, **When** I click "View message" on a task, **Then** I see the original message that triggered the task extraction.
2. **Given** I am viewing the original message, **When** I want to return to my tasks, **Then** I can easily navigate back to the task list.

---

### Edge Cases

- What happens when a task has no deadline? → The deadline field should be omitted (not shown as "null" or blank).
- What happens when a user has tasks from multiple sources (WhatsApp, Gmail)? → All tasks appear in the same list, sorted by priority.
- What happens when a task is snoozed but the snooze period expires while the user is offline? → When the user comes back online, the task should reappear.
- What happens when two users have identical task descriptions? → Each user sees only their own tasks due to user isolation.
- What happens when the AI extracts a task but the original message is deleted? → The task should still appear; the "View message" action should handle missing messages gracefully.
- What happens when a user tries to complete an already completed task? → The system should prevent duplicate completions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display only tasks belonging to the authenticated user (user isolation).
- **FR-002**: System MUST show each task with a priority indicator (🔴 for urgent, 🟡 for important, 🟢 for normal).
- **FR-003**: System MUST show task description and deadline (if available) for each task.
- **FR-004**: System MUST sort tasks by priority (urgent first, then important, then normal).
- **FR-005**: System MUST allow users to mark tasks as complete, which removes them from the active list.
- **FR-006**: System MUST allow users to snooze tasks for a defined period (1 hour, tomorrow, next week).
- **FR-007**: System MUST allow users to view the original message that created the task.
- **FR-008**: System MUST show a "No tasks found" message when no tasks exist.
- **FR-009**: System MUST preserve original task wording from AI extraction (no modifications).
- **FR-010**: System MUST handle missing deadlines gracefully (omit field, not show null).
- **FR-011**: System MUST provide visual feedback when tasks are completed.
- **FR-012**: System MUST load the task list within 1 second for up to 100 tasks.
- **FR-013**: System MUST work responsively on desktop and mobile widths.
- **FR-014**: System MUST make task actions keyboard navigable.

### Key Entities

- **Task**: Represents an extracted action item from a message. Key attributes: description, deadline, priority level, completion status, snooze status, source message reference.
- **User**: The authenticated person viewing tasks. Tasks are owned by exactly one user.
- **Message**: The original communication that triggered task extraction. Tasks reference their source message.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view all their tasks within 1 second of navigating to the Tasks page.
- **SC-002**: 100% of tasks displayed belong to the authenticated user (no cross-user data leakage).
- **SC-003**: Users can complete a task with one click and see visual confirmation within 500ms.
- **SC-004**: Task list loads correctly on both desktop and mobile screen sizes.
- **SC-005**: When no tasks exist, users see a helpful "No tasks found" message instead of a blank page.
- **SC-006**: Task priority indicators (🔴, 🟡, 🟢) accurately reflect the AI's classification.
- **SC-007**: Users can access the original message context for any task with one click.
- **SC-008**: Snoozed tasks reappear at the specified time without user intervention.

## Assumptions

- Tasks are already being extracted by the AI pipeline and stored in the database.
- The authentication system is already in place and working.
- Users have at least one communication channel connected (WhatsApp, Gmail, etc.).
- The AI priority classification (urgent, important, normal) is reliable.
- Task deadlines are either relative (Tonight, Tomorrow) or null - no complex date calculations needed.
- The "View message" action will navigate to the existing message detail view in the inbox.
- Snooze durations are fixed options (1 hour, tomorrow, next week) rather than custom date/time selection.