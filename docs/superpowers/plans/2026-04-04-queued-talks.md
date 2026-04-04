# Queued Talks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Queued Talks" feature where either partner can queue serious topics for weekend QT, with notes for prep. Also remove the curfew middleware entirely.

**Architecture:** Two new DB models (Talk, TalkNote), a new route module, a new frontend page at `/talks`, and dashboard integration. Curfew middleware and all emergency_override references removed across the stack.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Nuxt 4 (Vue 3), Tailwind CSS

---

### Task 1: Remove curfew middleware (backend)

**Files:**
- Delete: `backend/app/middleware.py`
- Delete: `backend/tests/test_curfew.py`
- Modify: `backend/app/main.py:8,38`
- Modify: `backend/app/schemas.py:47,67,72`

- [ ] **Step 1: Delete middleware file and curfew tests**

```bash
rm backend/app/middleware.py backend/tests/test_curfew.py
```

- [ ] **Step 2: Remove middleware from main.py**

In `backend/app/main.py`, remove the import line:
```python
from app.middleware import AdabCurfewMiddleware
```

And remove:
```python
app.add_middleware(AdabCurfewMiddleware)
```

- [ ] **Step 3: Remove emergency_override from schemas**

In `backend/app/schemas.py`, remove `emergency_override: bool = False` from:
- `RuleCreate` (line 47)
- `QuestionCreate` (line 67)
- `AnswerCreate` (line 72)

- [ ] **Step 4: Run existing tests to verify nothing breaks**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: All tests pass (curfew tests are gone, others unaffected since emergency_override was optional with a default).

- [ ] **Step 5: Commit**

```bash
git add -A backend/app/middleware.py backend/tests/test_curfew.py backend/app/main.py backend/app/schemas.py
git commit -m "refactor: remove curfew middleware and emergency_override from schemas"
```

---

### Task 2: Remove emergency override from frontend

**Files:**
- Delete: `frontend/app/components/EmergencyOverrideModal.vue`
- Modify: `frontend/app/pages/rules.vue`
- Modify: `frontend/app/pages/inquiry.vue`

- [ ] **Step 1: Delete the modal component**

```bash
rm frontend/app/components/EmergencyOverrideModal.vue
```

- [ ] **Step 2: Clean up rules.vue**

In `frontend/app/pages/rules.vue`, remove these state declarations:
```javascript
const showOverrideModal = ref(false)
const pendingAction = ref<(() => Promise<void>) | null>(null)
```

Simplify `createRule` — remove the `emergencyOverride` parameter and the 403 catch logic. Replace the entire function with:
```javascript
async function createRule() {
  await api('/rules', {
    method: 'POST',
    body: { title: newTitle.value, description: newDesc.value },
  })
  newTitle.value = ''
  newDesc.value = ''
  showNewForm.value = false
  await loadRules()
}
```

Remove the `handleOverrideConfirm` function entirely.

Update the form submit to `@submit.prevent="createRule"` (remove the arrow function wrapper).

Remove the `EmergencyOverrideModal` template block at the bottom of the template.

- [ ] **Step 3: Clean up inquiry.vue**

In `frontend/app/pages/inquiry.vue`, remove:
```javascript
const showOverrideModal = ref(false)
const pendingAction = ref<(() => Promise<void>) | null>(null)
```

Simplify `createQuestion` — remove the `emergencyOverride` parameter and 403 catch:
```javascript
async function createQuestion() {
  await api('/questions', {
    method: 'POST',
    body: { text: newText.value },
  })
  newText.value = ''
  showNewForm.value = false
  await loadQuestions()
}
```

Simplify `answerQuestion` — remove `emergencyOverride` parameter and 403 catch:
```javascript
async function answerQuestion(questionId: number, text: string) {
  await api(`/questions/${questionId}/answer`, {
    method: 'POST',
    body: { text },
  })
  await loadQuestions()
}
```

Remove `handleOverrideConfirm` function.

Update form submit to `@submit.prevent="createQuestion"`.

Remove the `EmergencyOverrideModal` template block.

- [ ] **Step 4: Commit**

```bash
git add -A frontend/app/components/EmergencyOverrideModal.vue frontend/app/pages/rules.vue frontend/app/pages/inquiry.vue
git commit -m "refactor: remove emergency override UI from rules and inquiry pages"
```

---

### Task 3: Add Talk and TalkNote models

**Files:**
- Modify: `backend/app/models.py`

- [ ] **Step 1: Add Talk and TalkNote models**

Append to the end of `backend/app/models.py`:

```python
class Talk(Base):
    __tablename__ = "talks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    proposer: Mapped["User"] = relationship("User", foreign_keys=[proposed_by])
    notes: Mapped[List["TalkNote"]] = relationship("TalkNote", back_populates="talk", cascade="all, delete-orphan")


class TalkNote(Base):
    __tablename__ = "talk_notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    talk_id: Mapped[int] = mapped_column(ForeignKey("talks.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    talk: Mapped["Talk"] = relationship("Talk", back_populates="notes")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
```

- [ ] **Step 2: Verify models load**

```bash
cd backend && python -c "from app.models import Talk, TalkNote; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/models.py
git commit -m "feat: add Talk and TalkNote database models"
```

---

### Task 4: Add Talk schemas

**Files:**
- Modify: `backend/app/schemas.py`

- [ ] **Step 1: Add Talk schemas**

Append before the `# Activity` section in `backend/app/schemas.py`:

```python
# --- Talks schemas ---

class TalkCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TalkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class TalkNoteCreate(BaseModel):
    text: str


class TalkNoteOut(BaseModel):
    id: int
    user_id: int
    username: str
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TalkOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    proposed_by: int
    proposer_name: str
    status: str
    notes: list[TalkNoteOut] = []
    note_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas.py
git commit -m "feat: add Talk and TalkNote Pydantic schemas"
```

---

### Task 5: Add talks route — write tests first

**Files:**
- Create: `backend/tests/test_talks.py`

- [ ] **Step 1: Write all talk tests**

Create `backend/tests/test_talks.py`:

```python
from tests.conftest import auth_header


def test_create_talk(client, alif_token):
    resp = client.post("/talks", json={"title": "Discuss wedding venue"}, headers=auth_header(alif_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Discuss wedding venue"
    assert data["status"] == "queued"
    assert data["proposer_name"] == "Alif"
    assert data["note_count"] == 0


def test_list_talks(client, alif_token):
    client.post("/talks", json={"title": "Talk A"}, headers=auth_header(alif_token))
    client.post("/talks", json={"title": "Talk B"}, headers=auth_header(alif_token))
    resp = client.get("/talks", headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_talks_queued_first(client, alif_token):
    # Create two talks, mark one as discussed
    client.post("/talks", json={"title": "Old talk"}, headers=auth_header(alif_token))
    resp2 = client.post("/talks", json={"title": "New talk"}, headers=auth_header(alif_token))
    talk_id = resp2.json()["id"]
    client.patch(f"/talks/{talk_id}", json={"status": "discussed"}, headers=auth_header(alif_token))

    resp = client.get("/talks", headers=auth_header(alif_token))
    talks = resp.json()
    # Queued talks should come before discussed
    assert talks[0]["status"] == "queued"
    assert talks[1]["status"] == "discussed"


def test_update_talk_status(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.patch(f"/talks/{talk_id}", json={"status": "discussed"}, headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "discussed"


def test_update_talk_status_follow_up(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.patch(f"/talks/{talk_id}", json={"status": "follow_up"}, headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "follow_up"


def test_update_talk_invalid_status(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.patch(f"/talks/{talk_id}", json={"status": "invalid"}, headers=auth_header(alif_token))
    assert resp.status_code == 400


def test_partner_can_update_status(client, alif_token, syifa_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.patch(f"/talks/{talk_id}", json={"status": "discussed"}, headers=auth_header(syifa_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "discussed"


def test_only_proposer_can_edit_title(client, alif_token, syifa_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.patch(f"/talks/{talk_id}", json={"title": "Changed"}, headers=auth_header(syifa_token))
    assert resp.status_code == 403


def test_delete_talk(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.delete(f"/talks/{talk_id}", headers=auth_header(alif_token))
    assert resp.status_code == 200

    resp = client.get("/talks", headers=auth_header(alif_token))
    assert len(resp.json()) == 0


def test_only_proposer_can_delete(client, alif_token, syifa_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.delete(f"/talks/{talk_id}", headers=auth_header(syifa_token))
    assert resp.status_code == 403


def test_cannot_delete_non_queued_talk(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]
    client.patch(f"/talks/{talk_id}", json={"status": "discussed"}, headers=auth_header(alif_token))

    resp = client.delete(f"/talks/{talk_id}", headers=auth_header(alif_token))
    assert resp.status_code == 400


def test_add_note(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.post(f"/talks/{talk_id}/notes", json={"text": "My thoughts"}, headers=auth_header(alif_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["note_count"] == 1
    assert data["notes"][0]["text"] == "My thoughts"


def test_partner_can_add_note(client, alif_token, syifa_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    client.post(f"/talks/{talk_id}/notes", json={"text": "Alif note"}, headers=auth_header(alif_token))
    resp = client.post(f"/talks/{talk_id}/notes", json={"text": "Syifa note"}, headers=auth_header(syifa_token))
    assert resp.json()["note_count"] == 2


def test_delete_own_note(client, alif_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.post(f"/talks/{talk_id}/notes", json={"text": "Note"}, headers=auth_header(alif_token))
    note_id = resp.json()["notes"][0]["id"]

    resp = client.delete(f"/talks/{talk_id}/notes/{note_id}", headers=auth_header(alif_token))
    assert resp.status_code == 200


def test_cannot_delete_partner_note(client, alif_token, syifa_token):
    resp = client.post("/talks", json={"title": "Topic"}, headers=auth_header(alif_token))
    talk_id = resp.json()["id"]

    resp = client.post(f"/talks/{talk_id}/notes", json={"text": "Alif note"}, headers=auth_header(alif_token))
    note_id = resp.json()["notes"][0]["id"]

    resp = client.delete(f"/talks/{talk_id}/notes/{note_id}", headers=auth_header(syifa_token))
    assert resp.status_code == 403
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && python -m pytest tests/test_talks.py -v
```

Expected: All tests FAIL (route doesn't exist yet).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_talks.py
git commit -m "test: add failing tests for talks feature"
```

---

### Task 6: Implement talks route

**Files:**
- Create: `backend/app/routes/talks.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create the talks route module**

Create `backend/app/routes/talks.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import case

from app.auth import get_current_user
from app.database import get_db
from app.models import Talk, TalkNote, User
from app.schemas import TalkCreate, TalkNoteCreate, TalkNoteOut, TalkOut, TalkUpdate

router = APIRouter(prefix="/talks", tags=["talks"])

VALID_STATUSES = {"queued", "discussed", "follow_up"}

STATUS_ORDER = case(
    (Talk.status == "queued", 0),
    (Talk.status == "follow_up", 1),
    (Talk.status == "discussed", 2),
    else_=3,
)


def note_to_out(note: TalkNote) -> TalkNoteOut:
    return TalkNoteOut(
        id=note.id,
        user_id=note.user_id,
        username=note.user.display_name,
        text=note.text,
        created_at=note.created_at,
    )


def talk_to_out(talk: Talk) -> TalkOut:
    return TalkOut(
        id=talk.id,
        title=talk.title,
        description=talk.description,
        proposed_by=talk.proposed_by,
        proposer_name=talk.proposer.display_name,
        status=talk.status,
        notes=[note_to_out(n) for n in talk.notes],
        note_count=len(talk.notes),
        created_at=talk.created_at,
    )


@router.get("", response_model=list[TalkOut])
def list_talks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    talks = (
        db.query(Talk)
        .order_by(STATUS_ORDER, Talk.created_at.desc())
        .all()
    )
    return [talk_to_out(t) for t in talks]


@router.post("", response_model=TalkOut, status_code=status.HTTP_201_CREATED)
def create_talk(
    body: TalkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    talk = Talk(
        title=body.title,
        description=body.description,
        proposed_by=current_user.id,
    )
    db.add(talk)
    db.commit()
    db.refresh(talk)
    return talk_to_out(talk)


@router.patch("/{talk_id}", response_model=TalkOut)
def update_talk(
    talk_id: int,
    body: TalkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    talk = db.query(Talk).filter(Talk.id == talk_id).first()
    if talk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talk not found")

    # Only proposer can edit title/description
    if (body.title is not None or body.description is not None) and talk.proposed_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the proposer can edit title and description")

    if body.status is not None:
        if body.status not in VALID_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
        talk.status = body.status

    if body.title is not None:
        talk.title = body.title
    if body.description is not None:
        talk.description = body.description

    db.commit()
    db.refresh(talk)
    return talk_to_out(talk)


@router.delete("/{talk_id}", response_model=TalkOut)
def delete_talk(
    talk_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    talk = db.query(Talk).filter(Talk.id == talk_id).first()
    if talk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talk not found")

    if talk.proposed_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the proposer can delete this talk")

    if talk.status != "queued":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only delete queued talks")

    out = talk_to_out(talk)
    db.delete(talk)
    db.commit()
    return out


@router.post("/{talk_id}/notes", response_model=TalkOut, status_code=status.HTTP_201_CREATED)
def add_note(
    talk_id: int,
    body: TalkNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    talk = db.query(Talk).filter(Talk.id == talk_id).first()
    if talk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Talk not found")

    note = TalkNote(
        talk_id=talk_id,
        user_id=current_user.id,
        text=body.text,
    )
    db.add(note)
    db.commit()
    db.refresh(talk)
    return talk_to_out(talk)


@router.delete("/{talk_id}/notes/{note_id}")
def delete_note(
    talk_id: int,
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = db.query(TalkNote).filter(TalkNote.id == note_id, TalkNote.talk_id == talk_id).first()
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    if note.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only delete your own notes")

    db.delete(note)
    db.commit()
    return {"ok": True}
```

- [ ] **Step 2: Register the route in main.py**

In `backend/app/main.py`, add:

Import:
```python
from app.routes.talks import router as talks_router
```

Register (after milestones_router):
```python
app.include_router(talks_router)
```

- [ ] **Step 3: Run all tests**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: All tests pass including the new talk tests.

- [ ] **Step 4: Commit**

```bash
git add backend/app/routes/talks.py backend/app/main.py
git commit -m "feat: implement talks API routes"
```

---

### Task 7: Add talk events to activity feed

**Files:**
- Modify: `backend/app/routes/activity.py`

- [ ] **Step 1: Add talk events to activity route**

In `backend/app/routes/activity.py`, add `Talk` to the model imports:

```python
from app.models import (
    Answer,
    Milestone,
    MilestoneApproval,
    Question,
    Rule,
    RuleSignature,
    Talk,
    User,
)
```

Add this block before `events.sort(...)`:

```python
    # Talk events
    talks = db.query(Talk).all()
    for talk in talks:
        events.append(ActivityOut(
            type="talk_queued",
            actor=talk.proposer.display_name,
            summary=f'Queued talk "{talk.title}"',
            timestamp=talk.created_at,
        ))
```

- [ ] **Step 2: Run tests**

```bash
cd backend && python -m pytest tests/test_activity.py -v
```

Expected: All activity tests pass.

- [ ] **Step 3: Commit**

```bash
git add backend/app/routes/activity.py
git commit -m "feat: add talk events to activity feed"
```

---

### Task 8: Frontend — add Talks nav item and dashboard card

**Files:**
- Modify: `frontend/app/components/NavBar.vue`
- Modify: `frontend/app/pages/index.vue`

- [ ] **Step 1: Add Talks to NavBar**

In `frontend/app/components/NavBar.vue`, add to the `navItems` array after the rules entry:

```javascript
{ path: '/talks', label: 'Talks', icon: '&#9993;' },
```

- [ ] **Step 2: Add Talk stats and quick action to dashboard**

In `frontend/app/pages/index.vue`:

Add the Talk interface:
```typescript
interface Talk {
  id: number
  status: string
}
```

Add state:
```typescript
const talks = ref<Talk[]>([])
```

Add computed:
```typescript
const talkStats = computed(() => {
  const queued = talks.value.filter(t => t.status === 'queued').length
  const followUp = talks.value.filter(t => t.status === 'follow_up').length
  return { queued, followUp, total: talks.value.length }
})
```

Update `loadAll` to fetch talks too:
```typescript
async function loadAll() {
  loading.value = true
  try {
    const [a, r, q, m, t] = await Promise.all([
      api<Activity[]>('/activity'),
      api<Rule[]>('/rules'),
      api<Question[]>('/questions'),
      api<Milestone[]>('/milestones'),
      api<Talk[]>('/talks'),
    ])
    activities.value = a.slice(0, 10)
    rules.value = r
    questions.value = q
    milestones.value = m
    talks.value = t
  } finally {
    loading.value = false
  }
}
```

Add activity icon for talks (in `activityIcon` function):
```typescript
talk_queued: 'bg-verse-slate',
```

Change the quick stats grid from `grid-cols-3` to `grid-cols-2 sm:grid-cols-4`, and add a 4th card after the Milestones card:

```html
<NuxtLink to="/talks" class="bg-white rounded-xl border border-verse-slate/10 p-4 hover:shadow-md transition">
  <p class="text-xs text-verse-text/50 mb-1">Talks</p>
  <p class="text-2xl font-serif text-verse-text">{{ talkStats.total }}</p>
  <div class="flex gap-2 mt-2 flex-wrap">
    <span class="stats-pill bg-verse-slate/10 text-verse-slate">{{ talkStats.queued }} queued</span>
    <span v-if="talkStats.followUp" class="stats-pill bg-verse-rose/10 text-verse-rose">{{ talkStats.followUp }} follow-up</span>
  </div>
</NuxtLink>
```

Add a 4th quick action after the milestone one:
```html
<NuxtLink to="/talks?new=1" class="flex-1 py-2.5 text-center text-sm rounded-lg border border-verse-slate/20 text-verse-slate hover:bg-verse-slate/5 transition">
  + Queue a Talk
</NuxtLink>
```

Update the loading skeleton stats grid to match `grid-cols-2 sm:grid-cols-4` and add a 4th skeleton card, and update the quick actions skeleton to 4 items.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/components/NavBar.vue frontend/app/pages/index.vue
git commit -m "feat: add Talks nav item and dashboard stats card"
```

---

### Task 9: Frontend — create Talks page

**Files:**
- Create: `frontend/app/pages/talks.vue`

- [ ] **Step 1: Create talks.vue**

Create `frontend/app/pages/talks.vue`:

```vue
<script setup lang="ts">
interface TalkNote {
  id: number
  user_id: number
  username: string
  text: string
  created_at: string
}

interface Talk {
  id: number
  title: string
  description: string | null
  proposed_by: number
  proposer_name: string
  status: string
  notes: TalkNote[]
  note_count: number
  created_at: string
}

const { user } = useAuth()
const { api } = useApi()
const route = useRoute()
const loading = ref(true)
const talks = ref<Talk[]>([])
const filter = ref<'all' | 'queued' | 'follow_up' | 'discussed'>('all')
const showNewForm = ref(false)
const newTitle = ref('')
const newDesc = ref('')
const expandedId = ref<number | null>(null)
const noteTexts = ref<Record<number, string>>({})

async function loadTalks() {
  try {
    talks.value = await api<Talk[]>('/talks')
  } finally {
    loading.value = false
  }
}

const filteredTalks = computed(() => {
  if (filter.value === 'all') return talks.value
  return talks.value.filter(t => t.status === filter.value)
})

const stats = computed(() => ({
  total: talks.value.length,
  queued: talks.value.filter(t => t.status === 'queued').length,
  followUp: talks.value.filter(t => t.status === 'follow_up').length,
  discussed: talks.value.filter(t => t.status === 'discussed').length,
}))

function statusBadge(status: string): { text: string; style: string } {
  switch (status) {
    case 'queued': return { text: 'Queued', style: 'bg-verse-slate text-white' }
    case 'discussed': return { text: 'Discussed', style: 'bg-verse-gold text-white' }
    case 'follow_up': return { text: 'Follow-up', style: 'bg-verse-rose text-white' }
    default: return { text: status, style: 'bg-verse-slate/20' }
  }
}

function proposerInitial(talk: Talk): string {
  return talk.proposer_name[0]
}

function proposerColor(talk: Talk): string {
  return talk.proposed_by === user.value?.id
    ? (user.value?.username === 'alif' ? 'bg-verse-slate' : 'bg-verse-rose')
    : (user.value?.username === 'alif' ? 'bg-verse-rose' : 'bg-verse-slate')
}

function noteAuthorColor(note: TalkNote): string {
  return note.user_id === user.value?.id
    ? (user.value?.username === 'alif' ? 'bg-verse-slate' : 'bg-verse-rose')
    : (user.value?.username === 'alif' ? 'bg-verse-rose' : 'bg-verse-slate')
}

async function createTalk() {
  await api('/talks', {
    method: 'POST',
    body: { title: newTitle.value, description: newDesc.value || null },
  })
  newTitle.value = ''
  newDesc.value = ''
  showNewForm.value = false
  await loadTalks()
}

async function updateStatus(talkId: number, status: string) {
  await api(`/talks/${talkId}`, {
    method: 'PATCH',
    body: { status },
  })
  await loadTalks()
}

async function deleteTalk(talkId: number) {
  await api(`/talks/${talkId}`, { method: 'DELETE' })
  await loadTalks()
}

async function addNote(talkId: number) {
  const text = noteTexts.value[talkId]?.trim()
  if (!text) return
  await api(`/talks/${talkId}/notes`, {
    method: 'POST',
    body: { text },
  })
  noteTexts.value[talkId] = ''
  await loadTalks()
}

async function deleteNote(talkId: number, noteId: number) {
  await api(`/talks/${talkId}/notes/${noteId}`, { method: 'DELETE' })
  await loadTalks()
}

onMounted(() => {
  loadTalks()
  if (route.query.new === '1') showNewForm.value = true
})
</script>

<template>
  <div>
    <!-- Loading skeleton -->
    <div v-if="loading" class="animate-pulse">
      <div class="flex justify-between mb-4">
        <div>
          <div class="h-8 bg-verse-slate/10 rounded w-40 mb-2" />
          <div class="h-4 bg-verse-slate/10 rounded w-56" />
        </div>
        <div class="h-10 bg-verse-slate/10 rounded w-28" />
      </div>
      <div class="flex gap-2 mb-4">
        <div v-for="i in 3" :key="i" class="h-6 bg-verse-slate/10 rounded-full w-20" />
      </div>
      <div class="space-y-3">
        <div v-for="i in 3" :key="i" class="bg-white rounded-xl border border-verse-slate/10 p-4">
          <div class="h-5 bg-verse-slate/10 rounded w-1/2 mb-2" />
          <div class="h-4 bg-verse-slate/10 rounded w-1/3" />
        </div>
      </div>
    </div>

    <template v-else>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-2 gap-3">
      <div>
        <h1 class="text-2xl font-serif text-verse-text">Queued Talks</h1>
        <div class="header-gradient-line w-14" />
        <p class="text-sm text-verse-text/50 mt-2">Save important topics for your weekend QT</p>
      </div>
      <button
        @click="showNewForm = !showNewForm"
        class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition w-full sm:w-auto"
      >
        {{ showNewForm ? 'Cancel' : '+ Queue Talk' }}
      </button>
    </div>

    <div class="flex gap-2 mb-4 flex-wrap">
      <span class="stats-pill bg-verse-slate/10 text-verse-text/60">{{ stats.total }} total</span>
      <span class="stats-pill bg-verse-slate/10 text-verse-slate">{{ stats.queued }} queued</span>
      <span v-if="stats.followUp" class="stats-pill bg-verse-rose/10 text-verse-rose">{{ stats.followUp }} follow-up</span>
    </div>

    <form v-if="showNewForm" @submit.prevent="createTalk" class="bg-white rounded-xl border border-verse-slate/10 p-4 sm:p-5 mb-6">
      <input v-model="newTitle" placeholder="What do you need to discuss?" required class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 text-sm" />
      <textarea v-model="newDesc" placeholder="Add context (optional)" rows="2" class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none text-sm" />
      <button type="submit" class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">Queue Talk</button>
    </form>

    <div class="flex gap-1 mb-4 bg-white rounded-lg p-1 border border-verse-slate/10 w-full sm:w-fit overflow-x-auto">
      <button
        v-for="f in (['all', 'queued', 'follow_up', 'discussed'] as const)"
        :key="f"
        @click="filter = f"
        class="flex-1 sm:flex-none px-3 py-1 text-sm rounded-md transition whitespace-nowrap"
        :class="filter === f ? 'bg-verse-slate text-white' : 'text-verse-text/60 hover:bg-verse-slate/5'"
      >
        {{ f === 'follow_up' ? 'Follow-up' : f.charAt(0).toUpperCase() + f.slice(1) }}
        <span class="ml-1 opacity-70">({{ f === 'all' ? stats.total : f === 'queued' ? stats.queued : f === 'follow_up' ? stats.followUp : stats.discussed }})</span>
      </button>
    </div>

    <div class="space-y-2">
      <div
        v-for="talk in filteredTalks"
        :key="talk.id"
        class="rounded-xl border p-4 transition bg-white border-verse-slate/10"
        :class="talk.status === 'discussed' ? 'opacity-60' : ''"
      >
        <div class="flex items-center justify-between gap-2 cursor-pointer" @click="expandedId = expandedId === talk.id ? null : talk.id">
          <div class="flex items-center gap-2 min-w-0 flex-1">
            <span class="avatar-dot shrink-0" :class="proposerColor(talk)">{{ proposerInitial(talk) }}</span>
            <span class="text-sm font-medium text-verse-text truncate">{{ talk.title }}</span>
            <span v-if="talk.note_count" class="text-xs text-verse-text/30">{{ talk.note_count }} notes</span>
          </div>
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium shrink-0"
            :class="statusBadge(talk.status).style"
          >
            {{ statusBadge(talk.status).text }}
          </span>
        </div>

        <div v-if="expandedId === talk.id" class="mt-3 pt-3 border-t border-verse-slate/5">
          <p v-if="talk.description" class="text-xs text-verse-text/60 mb-3">{{ talk.description }}</p>

          <!-- Notes -->
          <div v-if="talk.notes.length" class="space-y-2 mb-3">
            <div v-for="note in talk.notes" :key="note.id" class="flex items-start gap-2">
              <span class="avatar-dot text-[7px] mt-0.5 shrink-0" :class="noteAuthorColor(note)">{{ note.username[0] }}</span>
              <div class="flex-1 min-w-0">
                <p class="text-xs text-verse-text">{{ note.text }}</p>
                <p class="text-[10px] text-verse-text/30">{{ note.username }}</p>
              </div>
              <button
                v-if="note.user_id === user?.id"
                @click.stop="deleteNote(talk.id, note.id)"
                class="text-verse-text/20 hover:text-red-400 transition text-xs shrink-0"
              >&times;</button>
            </div>
          </div>

          <!-- Add note -->
          <form @submit.prevent="addNote(talk.id)" class="flex gap-2 mb-3">
            <input
              v-model="noteTexts[talk.id]"
              placeholder="Add a note..."
              class="flex-1 px-2.5 py-1.5 rounded-lg border border-verse-slate/15 text-xs focus:outline-none focus:ring-1 focus:ring-verse-slate/30"
              @click.stop
            />
            <button type="submit" class="px-3 py-1.5 bg-verse-slate/10 text-verse-slate text-xs rounded-lg hover:bg-verse-slate/20 transition" @click.stop>Add</button>
          </form>

          <!-- Actions -->
          <div class="flex flex-wrap gap-2">
            <button
              v-if="talk.status !== 'discussed'"
              @click.stop="updateStatus(talk.id, 'discussed')"
              class="text-xs px-3 py-1 rounded-full bg-verse-gold/10 text-verse-gold hover:bg-verse-gold/20 transition"
            >Mark Discussed</button>
            <button
              v-if="talk.status !== 'follow_up'"
              @click.stop="updateStatus(talk.id, 'follow_up')"
              class="text-xs px-3 py-1 rounded-full bg-verse-rose/10 text-verse-rose hover:bg-verse-rose/20 transition"
            >Needs Follow-up</button>
            <button
              v-if="talk.status !== 'queued'"
              @click.stop="updateStatus(talk.id, 'queued')"
              class="text-xs px-3 py-1 rounded-full bg-verse-slate/10 text-verse-slate hover:bg-verse-slate/20 transition"
            >Re-queue</button>
            <button
              v-if="talk.proposed_by === user?.id && talk.status === 'queued'"
              @click.stop="deleteTalk(talk.id)"
              class="text-xs text-red-400 ml-auto"
            >Delete</button>
          </div>
        </div>
      </div>

      <p v-if="filteredTalks.length === 0" class="text-center text-verse-text/40 py-8">
        No talks match this filter.
      </p>
    </div>
    </template>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/pages/talks.vue
git commit -m "feat: add Queued Talks frontend page"
```

---

### Task 10: Final verification

- [ ] **Step 1: Run all backend tests**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: Build frontend**

```bash
cd frontend && npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 3: Final commit and push**

```bash
git push origin master
```
