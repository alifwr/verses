# Queued Talks — Design Spec

## Purpose

When a serious matter comes up mid-week that needs more time to discuss, either partner queues it as a "Talk" for their weekend quality time (QT). This prevents rushed conversations and ensures important topics get proper attention.

## Data Model

### Talk

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, indexed |
| title | String(200) | Required |
| description | Text | Nullable |
| proposed_by | Integer | FK to users.id |
| status | String(20) | Default "queued". Values: "queued", "discussed", "follow_up" |
| created_at | DateTime | Default utcnow |

Relationships: `proposer` (User), `notes` (TalkNote, cascade delete-orphan)

### TalkNote

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, indexed |
| talk_id | Integer | FK to talks.id |
| user_id | Integer | FK to users.id |
| text | Text | Required |
| created_at | DateTime | Default utcnow |

Relationships: `talk` (Talk), `user` (User)

## Pydantic Schemas

### Input

- **TalkCreate**: `title` (str), `description` (str, optional)
- **TalkUpdate**: `title` (str, optional), `description` (str, optional), `status` (str, optional — must be one of "queued", "discussed", "follow_up")
- **TalkNoteCreate**: `text` (str)

### Output

- **TalkNoteOut**: `id`, `user_id`, `username`, `text`, `created_at`
- **TalkOut**: `id`, `title`, `description`, `proposed_by`, `proposer_name`, `status`, `notes` (list of TalkNoteOut), `note_count`, `created_at`

## API Endpoints

All endpoints require authentication via `get_current_user`.

### GET /talks

List all talks. Ordered by: status priority (queued first, follow_up second, discussed last), then `created_at DESC` within each group.

Response: list of `TalkOut`.

### POST /talks (201)

Create a new talk with status "queued".

Body: `TalkCreate`. Response: `TalkOut`.

### PATCH /talks/{talk_id}

Update a talk's title, description, or status.

Body: `TalkUpdate`. Response: `TalkOut`.

Either partner can change the status (since both participate in the QT discussion). Only proposer can edit title/description.

### DELETE /talks/{talk_id}

Delete a talk. Only the proposer can delete. Only allowed when status is "queued" (discussed/follow_up talks are kept as records).

Response: deleted `TalkOut`. Error: 403 if not proposer, 400 if not queued.

### POST /talks/{talk_id}/notes (201)

Add a note to a talk. Either partner can add notes.

Body: `TalkNoteCreate`. Response: `TalkOut` (full talk with updated notes).

### DELETE /talks/{talk_id}/notes/{note_id}

Delete a note. Only the note author can delete their own note.

Error: 403 if not author, 404 if not found.

## Activity Feed Events

Add these event types to the activity aggregation in `routes/activity.py`:

- `talk_queued` — "{proposer} queued a talk: {title}"
- `talk_discussed` — "{actor} marked talk as discussed: {title}"
- `talk_followed_up` — "{actor} marked talk for follow-up: {title}"

## Frontend

### Navigation

Add nav item: `{ path: '/talks', label: 'Talks', icon: '&#9993;' }` (envelope icon) in NavBar.vue.

### Page: `/talks` (talks.vue)

**Header**: "Queued Talks" with subtitle "Save important topics for your weekend QT".

**Stats pills**: total, queued count, follow-up count.

**Filter tabs**: All / Queued / Follow-up / Discussed.

**New talk form**: Title input + optional description textarea. Triggered by "+ Queue Talk" button.

**Talk cards** (mobile and desktop):
- Title, status badge (color-coded: queued=slate, discussed=gold, follow-up=rose)
- Proposer avatar + name
- Note count indicator
- Expandable section showing:
  - Description
  - Notes from both partners (each with author avatar, text, timestamp)
  - "Add note" input
  - Status action buttons: "Mark Discussed" / "Needs Follow-up" / "Re-queue"
  - Delete button (proposer only, queued only)

**Loading skeleton**: Same pattern as other pages (animate-pulse placeholders).

### Dashboard (index.vue)

Add a stats card for Talks alongside Rules/Questions/Milestones:
- Link to `/talks`
- Show total count, queued count, follow-up count
- Quick action: "+ Queue a Talk" linking to `/talks?new=1`

## Curfew Middleware Removal

Remove the `AdabCurfewMiddleware` entirely:

1. Delete `backend/app/middleware.py`
2. Remove `from app.middleware import AdabCurfewMiddleware` and `app.add_middleware(AdabCurfewMiddleware)` from `main.py`
3. Remove `emergency_override` field from `RuleCreate`, `QuestionCreate`, and `AnswerCreate` schemas
4. Remove emergency override handling from Rules and Questions route handlers (the `emergency_override` parameter in request bodies and the 403 catch logic)
5. Remove `EmergencyOverrideModal` component from frontend
6. Remove emergency override logic from `rules.vue`, `inquiry.vue` pages (the `showOverrideModal`, `pendingAction`, `handleOverrideConfirm` state and template)
7. Delete curfew tests (`test_curfew.py`)
8. Update existing tests that pass `emergency_override` in request bodies

## Testing

New test file: `tests/test_talks.py`

- Create a talk
- List talks (verify ordering: queued first)
- Add note to talk
- Delete own note
- Cannot delete partner's note
- Update talk status to discussed
- Update talk status to follow_up
- Re-queue a discussed talk
- Only proposer can delete
- Cannot delete non-queued talk
- Talk appears in activity feed
