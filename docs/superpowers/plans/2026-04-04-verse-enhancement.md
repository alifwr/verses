# Verse UI Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance Verse with auto-approve logic, a global activity feed, a dashboard landing page, a redesigned ledger table view, and richer visual design across all pages.

**Architecture:** Backend gets two changes (auto-approve on create, new /activity endpoint). Frontend gets a new dashboard page, a table-based ledger, visual enrichment (background textures, stats banners, left-border accents, avatar indicators, gradient timeline), and NavBar update.

**Tech Stack:** FastAPI, SQLAlchemy, Nuxt 4, Tailwind CSS, TypeScript

---

## File Structure

### Backend modifications
```
backend/app/routes/rules.py         — Modify: auto-create RuleSignature on create
backend/app/routes/milestones.py    — Modify: auto-create MilestoneApproval on create
backend/app/routes/activity.py      — Create: GET /activity endpoint
backend/app/schemas.py              — Modify: add ActivityOut schema
backend/app/main.py                 — Modify: mount activity router
backend/tests/test_rules.py         — Modify: update tests for auto-sign
backend/tests/test_milestones.py    — Modify: update tests for auto-approve
backend/tests/test_activity.py      — Create: activity endpoint tests
```

### Frontend modifications
```
frontend/app/pages/index.vue           — Rewrite: dashboard page
frontend/app/pages/ledger.vue          — Rewrite: table view
frontend/app/pages/inquiry.vue         — Modify: stats banner + visual enhancements
frontend/app/pages/roadmap.vue         — Modify: stats banner + progress bar
frontend/app/components/NavBar.vue     — Modify: add Home item, partner status dot
frontend/app/components/RuleCard.vue   — Delete (replaced by table rows in ledger.vue)
frontend/app/components/QuestionCard.vue — Modify: left-border accent, avatar dots, pulse button
frontend/app/components/MilestoneCard.vue — Modify: gradient timeline, checkmark, avatar dots
frontend/app/layouts/default.vue       — Modify: add background texture
frontend/app/assets/css/main.css       — Modify: add pulse animation, utility classes
```

---

## Task 1: Backend Auto-Approve for Proposer

**Files:**
- Modify: `backend/app/routes/rules.py`
- Modify: `backend/app/routes/milestones.py`
- Modify: `backend/tests/test_rules.py`
- Modify: `backend/tests/test_milestones.py`

- [ ] **Step 1: Update test_rules.py for auto-sign behavior**

Replace the test file content. Key changes: `test_create_rule` now expects `is_agreed_by_me=True`, `test_sign_rule` no longer needs alif to sign (auto-signed), partner sign directly seals.

```python
from tests.conftest import auth_header


def test_create_rule(client, alif_token):
    resp = client.post(
        "/rules",
        json={"title": "No late calls", "description": "Calls end by 9 PM"},
        headers=auth_header(alif_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "No late calls"
    assert data["is_sealed"] is False
    assert data["is_agreed_by_me"] is True  # Auto-signed by proposer
    assert data["is_agreed_by_partner"] is False


def test_list_rules(client, alif_token):
    client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    resp = client.get("/rules", headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_partner_sign_seals_rule(client, alif_token, syifa_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]

    # Alif already auto-signed, check from alif's perspective
    resp = client.get("/rules", headers=auth_header(alif_token))
    rule = [r for r in resp.json() if r["id"] == rule_id][0]
    assert rule["is_agreed_by_me"] is True
    assert rule["is_agreed_by_partner"] is False
    assert rule["is_sealed"] is False

    # Syifa signs -> sealed (because proposer already auto-signed)
    resp = client.post(f"/rules/{rule_id}/sign", headers=auth_header(syifa_token))
    assert resp.status_code == 200

    resp = client.get("/rules", headers=auth_header(alif_token))
    rule = [r for r in resp.json() if r["id"] == rule_id][0]
    assert rule["is_sealed"] is True


def test_proposer_cannot_double_sign(client, alif_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]
    # Proposer already auto-signed, trying to sign again should fail
    resp = client.post(f"/rules/{rule_id}/sign", headers=auth_header(alif_token))
    assert resp.status_code == 400


def test_delete_rule_by_proposer(client, alif_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]
    resp = client.delete(f"/rules/{rule_id}", headers=auth_header(alif_token))
    assert resp.status_code == 200


def test_cannot_delete_sealed_rule(client, alif_token, syifa_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]
    client.post(f"/rules/{rule_id}/sign", headers=auth_header(syifa_token))
    resp = client.delete(f"/rules/{rule_id}", headers=auth_header(alif_token))
    assert resp.status_code == 400


def test_cannot_delete_rule_by_non_proposer(client, alif_token, syifa_token):
    create = client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    rule_id = create.json()["id"]
    resp = client.delete(f"/rules/{rule_id}", headers=auth_header(syifa_token))
    assert resp.status_code == 403
```

- [ ] **Step 2: Update create_rule in routes/rules.py to auto-sign**

In `backend/app/routes/rules.py`, modify the `create_rule` function to add a RuleSignature for the proposer after creating the rule:

```python
@router.post("", response_model=RuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(
    body: RuleCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    rule = Rule(
        title=body.title,
        description=body.description,
        proposed_by=current_user.id,
    )
    db.add(rule)
    db.flush()

    # Auto-sign for proposer
    sig = RuleSignature(rule_id=rule.id, user_id=current_user.id)
    db.add(sig)

    db.commit()
    db.refresh(rule)
    return rule_to_out(rule, current_user.id, current_user.partner_id)
```

- [ ] **Step 3: Run rules tests**

```bash
cd /home/seratusjuta/verses/backend && source venv/bin/activate && pytest tests/test_rules.py -v
```

Expected: All 7 tests pass.

- [ ] **Step 4: Update test_milestones.py for auto-approve behavior**

```python
from tests.conftest import auth_header


def test_create_milestone(client, alif_token):
    resp = client.post(
        "/milestones",
        json={"title": "Get engaged", "description": "Propose formally", "target_date": "2027-01-01"},
        headers=auth_header(alif_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Get engaged"
    assert data["is_confirmed"] is False
    assert data["is_approved_by_me"] is True  # Auto-approved by proposer
    assert data["is_approved_by_partner"] is False


def test_list_milestones(client, alif_token):
    client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    resp = client.get("/milestones", headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_partner_approve_confirms_milestone(client, alif_token, syifa_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]

    # Alif already auto-approved
    resp = client.get("/milestones", headers=auth_header(alif_token))
    m = [x for x in resp.json() if x["id"] == mid][0]
    assert m["is_approved_by_me"] is True
    assert m["is_confirmed"] is False

    # Syifa approves -> confirmed
    client.post(f"/milestones/{mid}/approve", headers=auth_header(syifa_token))
    resp = client.get("/milestones", headers=auth_header(alif_token))
    m = [x for x in resp.json() if x["id"] == mid][0]
    assert m["is_confirmed"] is True


def test_proposer_cannot_double_approve(client, alif_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]
    resp = client.post(f"/milestones/{mid}/approve", headers=auth_header(alif_token))
    assert resp.status_code == 400


def test_update_milestone(client, alif_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]
    resp = client.patch(f"/milestones/{mid}", json={"is_completed": True}, headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert resp.json()["is_completed"] is True


def test_delete_milestone_by_proposer(client, alif_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]
    resp = client.delete(f"/milestones/{mid}", headers=auth_header(alif_token))
    assert resp.status_code == 200


def test_cannot_delete_confirmed_milestone(client, alif_token, syifa_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]
    client.post(f"/milestones/{mid}/approve", headers=auth_header(syifa_token))
    resp = client.delete(f"/milestones/{mid}", headers=auth_header(alif_token))
    assert resp.status_code == 400
```

- [ ] **Step 5: Update create_milestone in routes/milestones.py to auto-approve**

In `backend/app/routes/milestones.py`, modify the `create_milestone` function:

```python
@router.post("", response_model=MilestoneOut, status_code=status.HTTP_201_CREATED)
def create_milestone(
    body: MilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    milestone = Milestone(
        title=body.title,
        description=body.description,
        target_date=body.target_date,
        proposed_by=current_user.id,
    )
    db.add(milestone)
    db.flush()

    # Auto-approve for proposer
    approval = MilestoneApproval(milestone_id=milestone.id, user_id=current_user.id)
    db.add(approval)

    db.commit()
    db.refresh(milestone)
    return milestone_to_out(milestone, current_user.id, current_user.partner_id)
```

- [ ] **Step 6: Run all backend tests**

```bash
cd /home/seratusjuta/verses/backend && source venv/bin/activate && pytest -v
```

Expected: All tests pass (auth: 6, curfew: 4, rules: 7, questions: 5, milestones: 7 = 29 total).

- [ ] **Step 7: Commit**

```bash
git add backend/ && git commit -m "feat(backend): auto-approve for proposer on rules and milestones"
```

---

## Task 2: Backend Activity Feed Endpoint

**Files:**
- Modify: `backend/app/schemas.py` (add ActivityOut)
- Create: `backend/app/routes/activity.py`
- Modify: `backend/app/main.py` (mount router)
- Create: `backend/tests/test_activity.py`

- [ ] **Step 1: Add ActivityOut schema to schemas.py**

Append to the end of `backend/app/schemas.py`:

```python
# Activity
class ActivityOut(BaseModel):
    type: str
    actor: str
    summary: str
    timestamp: datetime
```

- [ ] **Step 2: Write activity tests**

Create `backend/tests/test_activity.py`:

```python
from tests.conftest import auth_header


def test_activity_empty(client, alif_token):
    resp = client.get("/activity", headers=auth_header(alif_token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_activity_after_rule_created(client, alif_token):
    client.post("/rules", json={"title": "R1", "description": "D1"}, headers=auth_header(alif_token))
    resp = client.get("/activity", headers=auth_header(alif_token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    types = [a["type"] for a in data]
    assert "rule_created" in types


def test_activity_after_question_and_answer(client, alif_token, syifa_token):
    create = client.post("/questions", json={"text": "Q1"}, headers=auth_header(alif_token))
    qid = create.json()["id"]
    client.post(f"/questions/{qid}/answer", json={"text": "A1"}, headers=auth_header(alif_token))
    client.post(f"/questions/{qid}/answer", json={"text": "A2"}, headers=auth_header(syifa_token))

    resp = client.get("/activity", headers=auth_header(alif_token))
    data = resp.json()
    types = [a["type"] for a in data]
    assert "question_asked" in types
    assert "answer_submitted" in types
    assert "answers_revealed" in types


def test_activity_after_milestone_confirmed(client, alif_token, syifa_token):
    create = client.post("/milestones", json={"title": "M1", "description": "D1"}, headers=auth_header(alif_token))
    mid = create.json()["id"]
    client.post(f"/milestones/{mid}/approve", headers=auth_header(syifa_token))

    resp = client.get("/activity", headers=auth_header(alif_token))
    data = resp.json()
    types = [a["type"] for a in data]
    assert "milestone_proposed" in types
    assert "milestone_confirmed" in types


def test_activity_limit_20(client, alif_token):
    for i in range(25):
        client.post("/rules", json={"title": f"R{i}", "description": f"D{i}"}, headers=auth_header(alif_token))
    resp = client.get("/activity", headers=auth_header(alif_token))
    assert len(resp.json()) <= 20
```

- [ ] **Step 3: Create routes/activity.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    Answer,
    Milestone,
    MilestoneApproval,
    Question,
    Rule,
    RuleSignature,
    User,
)
from app.schemas import ActivityOut

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=list[ActivityOut])
def get_activity(
    current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)
):
    events: list[ActivityOut] = []

    # Rule events
    rules = db.query(Rule).all()
    for rule in rules:
        events.append(ActivityOut(
            type="rule_created",
            actor=rule.proposer.display_name,
            summary=f'Proposed rule "{rule.title}"',
            timestamp=rule.created_at,
        ))
        for sig in rule.signatures:
            # Skip auto-sign by proposer
            if sig.user_id == rule.proposed_by:
                continue
            events.append(ActivityOut(
                type="rule_sealed" if rule.is_sealed else "rule_signed",
                actor=sig.user.display_name,
                summary=f'Rule "{rule.title}" has been sealed' if rule.is_sealed else f'Signed rule "{rule.title}"',
                timestamp=sig.signed_at,
            ))

    # Question events
    questions = db.query(Question).all()
    for question in questions:
        events.append(ActivityOut(
            type="question_asked",
            actor=question.asker.display_name,
            summary=f'Asked "{question.text[:60]}"',
            timestamp=question.created_at,
        ))
        for answer in question.answers:
            events.append(ActivityOut(
                type="answer_submitted",
                actor=answer.user.display_name,
                summary=f'Answered "{question.text[:40]}..."',
                timestamp=answer.created_at,
            ))
        # Check if both answered (revealed)
        if len(question.answers) >= 2:
            latest = max(a.created_at for a in question.answers)
            events.append(ActivityOut(
                type="answers_revealed",
                actor="Both",
                summary=f'Answers revealed for "{question.text[:40]}..."',
                timestamp=latest,
            ))

    # Milestone events
    milestones = db.query(Milestone).all()
    for milestone in milestones:
        events.append(ActivityOut(
            type="milestone_proposed",
            actor=milestone.proposer.display_name,
            summary=f'Proposed milestone "{milestone.title}"',
            timestamp=milestone.created_at,
        ))
        for approval in milestone.approvals:
            # Skip auto-approve by proposer
            if approval.user_id == milestone.proposed_by:
                continue
            if milestone.is_confirmed:
                events.append(ActivityOut(
                    type="milestone_confirmed",
                    actor=approval.user.display_name,
                    summary=f'Milestone "{milestone.title}" confirmed',
                    timestamp=approval.approved_at,
                ))
            else:
                events.append(ActivityOut(
                    type="milestone_approved",
                    actor=approval.user.display_name,
                    summary=f'Approved milestone "{milestone.title}"',
                    timestamp=approval.approved_at,
                ))
        if milestone.is_completed:
            events.append(ActivityOut(
                type="milestone_completed",
                actor=milestone.proposer.display_name,
                summary=f'Milestone "{milestone.title}" completed',
                timestamp=milestone.created_at,
            ))

    # Sort by timestamp desc, limit 20
    events.sort(key=lambda e: e.timestamp, reverse=True)
    return events[:20]
```

- [ ] **Step 4: Mount activity router in main.py**

Add to `backend/app/main.py`:

```python
from app.routes.activity import router as activity_router
app.include_router(activity_router)
```

- [ ] **Step 5: Run activity tests**

```bash
cd /home/seratusjuta/verses/backend && source venv/bin/activate && pytest tests/test_activity.py -v
```

Expected: All 5 tests pass.

- [ ] **Step 6: Run full backend test suite**

```bash
cd /home/seratusjuta/verses/backend && source venv/bin/activate && pytest -v
```

Expected: All 34 tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/ && git commit -m "feat(backend): global activity feed endpoint"
```

---

## Task 3: Frontend Visual Foundation (CSS + Layout + NavBar)

**Files:**
- Modify: `frontend/app/assets/css/main.css`
- Modify: `frontend/app/layouts/default.vue`
- Modify: `frontend/app/components/NavBar.vue`

- [ ] **Step 1: Update main.css with new animations and utilities**

Replace `frontend/app/assets/css/main.css` with:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-verse-bg text-verse-text font-sans;
  }

  h1, h2, h3, h4 {
    @apply font-serif;
  }
}

@layer components {
  .header-gradient-line {
    @apply h-0.5 mt-2 rounded-full;
    background: linear-gradient(to right, #6B7FA3, #C5A55A);
  }

  .stats-pill {
    @apply px-3 py-1 rounded-full text-xs font-medium;
  }

  .avatar-dot {
    @apply w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold text-white;
  }
}

@layer utilities {
  .animate-soft-pulse {
    animation: soft-pulse 2.5s ease-in-out infinite;
  }

  @keyframes soft-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
}
```

- [ ] **Step 2: Update default.vue with background texture**

Replace `frontend/app/layouts/default.vue` with:

```vue
<template>
  <div class="min-h-screen bg-verse-bg relative">
    <!-- Topographic background texture -->
    <div class="fixed inset-0 pointer-events-none z-0">
      <svg class="w-full h-full opacity-[0.03]">
        <pattern id="topo-bg" width="120" height="120" patternUnits="userSpaceOnUse">
          <circle cx="60" cy="60" r="50" fill="none" stroke="#6B7FA3" stroke-width="0.5"/>
          <circle cx="60" cy="60" r="35" fill="none" stroke="#6B7FA3" stroke-width="0.5"/>
          <circle cx="60" cy="60" r="20" fill="none" stroke="#6B7FA3" stroke-width="0.5"/>
        </pattern>
        <rect width="100%" height="100%" fill="url(#topo-bg)"/>
      </svg>
    </div>

    <NavBar />
    <main class="relative z-10 max-w-4xl mx-auto px-4 py-6 pb-20 sm:pb-6">
      <slot />
    </main>
  </div>
</template>
```

- [ ] **Step 3: Update NavBar.vue with Home item and partner status**

Replace `frontend/app/components/NavBar.vue` with:

```vue
<script setup lang="ts">
const { user, logout } = useAuth()
const route = useRoute()

const navItems = [
  { path: '/', label: 'Home', icon: '&#9679;' },
  { path: '/ledger', label: 'Ledger', icon: '&#9874;' },
  { path: '/inquiry', label: 'Inquiry', icon: '&#10067;' },
  { path: '/roadmap', label: 'Roadmap', icon: '&#9670;' },
]

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const userColor = computed(() =>
  user.value?.username === 'alif' ? 'bg-verse-slate' : 'bg-verse-rose'
)

const partnerOnline = computed(() => user.value?.partner?.is_online ?? false)
</script>

<template>
  <!-- Desktop/tablet top nav -->
  <nav class="hidden sm:block bg-white/90 backdrop-blur-sm border-b border-verse-slate/10 sticky top-0 z-40">
    <div class="max-w-4xl mx-auto px-4 flex items-center justify-between h-14">
      <NuxtLink to="/" class="font-serif text-xl text-verse-text tracking-wide">Verse</NuxtLink>

      <div class="flex items-center gap-1">
        <NuxtLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="px-3 py-1.5 rounded-lg text-sm transition relative"
          :class="isActive(item.path) ? 'bg-verse-slate text-white' : 'text-verse-text hover:bg-verse-slate/10'"
        >
          {{ item.label }}
          <span v-if="isActive(item.path)" class="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-0.5 bg-verse-gold rounded-full" />
        </NuxtLink>
      </div>

      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <div class="relative">
            <span class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-medium" :class="userColor">
              {{ user?.display_name?.[0] }}
            </span>
            <span
              class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-white"
              :class="partnerOnline ? 'bg-green-400' : 'bg-verse-slate/30'"
              :title="partnerOnline ? 'Partner online' : 'Partner offline'"
            />
          </div>
          <span class="text-sm text-verse-text">{{ user?.display_name }}</span>
        </div>
        <button @click="logout" class="text-xs text-verse-slate hover:text-verse-text transition">
          Logout
        </button>
      </div>
    </div>
  </nav>

  <!-- Mobile top bar -->
  <div class="sm:hidden bg-white/90 backdrop-blur-sm border-b border-verse-slate/10 sticky top-0 z-40">
    <div class="px-4 flex items-center justify-between h-12">
      <span class="font-serif text-lg text-verse-text">Verse</span>
      <div class="flex items-center gap-2">
        <div class="relative">
          <span class="w-6 h-6 rounded-full flex items-center justify-center text-white text-[10px] font-medium" :class="userColor">
            {{ user?.display_name?.[0] }}
          </span>
          <span
            class="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full border border-white"
            :class="partnerOnline ? 'bg-green-400' : 'bg-verse-slate/30'"
          />
        </div>
        <button @click="logout" class="text-xs text-verse-slate">Logout</button>
      </div>
    </div>
  </div>

  <!-- Mobile bottom nav -->
  <nav class="sm:hidden fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-sm border-t border-verse-slate/10 z-40">
    <div class="flex items-center justify-around h-14 px-2">
      <NuxtLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition relative"
        :class="isActive(item.path) ? 'text-verse-slate' : 'text-verse-text/40'"
      >
        <span class="text-lg" v-html="item.icon" />
        <span class="text-[10px] font-medium">{{ item.label }}</span>
        <span v-if="isActive(item.path)" class="absolute -bottom-1 w-4 h-0.5 bg-verse-gold rounded-full" />
      </NuxtLink>
    </div>
  </nav>
</template>
```

- [ ] **Step 4: Verify frontend builds**

```bash
cd /home/seratusjuta/verses/frontend && npx nuxt build 2>&1 | tail -10
```

Expected: Build complete.

- [ ] **Step 5: Commit**

```bash
cd /home/seratusjuta/verses && git add frontend/ && git commit -m "feat(frontend): visual foundation - background texture, nav update, CSS utilities"
```

---

## Task 4: Frontend Dashboard Page

**Files:**
- Rewrite: `frontend/app/pages/index.vue`

- [ ] **Step 1: Replace index.vue with dashboard**

Replace `frontend/app/pages/index.vue` with:

```vue
<script setup lang="ts">
interface Activity {
  type: string
  actor: string
  summary: string
  timestamp: string
}

interface Rule {
  id: number
  is_sealed: boolean
  is_agreed_by_me: boolean
}

interface Question {
  id: number
  my_answer: any
  partner_answer: any
}

interface Milestone {
  id: number
  is_confirmed: boolean
  is_completed: boolean
}

const { user } = useAuth()
const { api } = useApi()

const activities = ref<Activity[]>([])
const rules = ref<Rule[]>([])
const questions = ref<Question[]>([])
const milestones = ref<Milestone[]>([])

const ruleStats = computed(() => {
  const sealed = rules.value.filter(r => r.is_sealed).length
  const pending = rules.value.filter(r => !r.is_agreed_by_me && !r.is_sealed).length
  return { sealed, pending, total: rules.value.length }
})

const questionStats = computed(() => {
  const revealed = questions.value.filter(q => q.my_answer && q.partner_answer).length
  const awaiting = questions.value.filter(q => !q.my_answer).length
  return { revealed, awaiting, total: questions.value.length }
})

const milestoneStats = computed(() => {
  const completed = milestones.value.filter(m => m.is_completed).length
  const confirmed = milestones.value.filter(m => m.is_confirmed && !m.is_completed).length
  const total = milestones.value.length
  return { completed, confirmed, total }
})

function relativeTime(ts: string): string {
  const now = new Date()
  const then = new Date(ts)
  const diff = Math.floor((now.getTime() - then.getTime()) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`
  return then.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function activityIcon(type: string): string {
  const icons: Record<string, string> = {
    rule_created: 'bg-verse-slate',
    rule_signed: 'bg-verse-slate',
    rule_sealed: 'bg-verse-gold',
    question_asked: 'bg-verse-slate',
    answer_submitted: 'bg-verse-rose',
    answers_revealed: 'bg-verse-gold',
    milestone_proposed: 'bg-verse-slate',
    milestone_approved: 'bg-verse-slate',
    milestone_confirmed: 'bg-verse-gold',
    milestone_completed: 'bg-green-500',
  }
  return icons[type] || 'bg-verse-slate/30'
}

async function loadAll() {
  const [a, r, q, m] = await Promise.all([
    api<Activity[]>('/activity'),
    api<Rule[]>('/rules'),
    api<Question[]>('/questions'),
    api<Milestone[]>('/milestones'),
  ])
  activities.value = a.slice(0, 10)
  rules.value = r
  questions.value = q
  milestones.value = m
}

onMounted(loadAll)
</script>

<template>
  <div>
    <!-- Welcome header -->
    <div class="mb-6">
      <h1 class="text-2xl font-serif text-verse-text">
        Welcome back, {{ user?.display_name }}
      </h1>
      <div class="header-gradient-line w-16" />
      <p class="text-sm text-verse-text/50 mt-2 flex items-center gap-2">
        <span
          class="w-2 h-2 rounded-full inline-block"
          :class="user?.partner?.is_online ? 'bg-green-400' : 'bg-verse-slate/30'"
        />
        {{ user?.partner?.display_name }} is {{ user?.partner?.is_online ? 'online' : 'offline' }}
      </p>
    </div>

    <!-- Quick stats -->
    <div class="grid grid-cols-3 gap-3 mb-6">
      <NuxtLink to="/ledger" class="bg-white rounded-xl border border-verse-slate/10 p-4 hover:shadow-md transition">
        <p class="text-xs text-verse-text/50 mb-1">Rules</p>
        <p class="text-2xl font-serif text-verse-text">{{ ruleStats.total }}</p>
        <div class="flex gap-2 mt-2">
          <span class="stats-pill bg-verse-gold/10 text-verse-gold">{{ ruleStats.sealed }} sealed</span>
          <span v-if="ruleStats.pending" class="stats-pill bg-verse-slate/10 text-verse-slate">{{ ruleStats.pending }} pending</span>
        </div>
      </NuxtLink>

      <NuxtLink to="/inquiry" class="bg-white rounded-xl border border-verse-slate/10 p-4 hover:shadow-md transition">
        <p class="text-xs text-verse-text/50 mb-1">Questions</p>
        <p class="text-2xl font-serif text-verse-text">{{ questionStats.total }}</p>
        <div class="flex gap-2 mt-2">
          <span class="stats-pill bg-verse-gold/10 text-verse-gold">{{ questionStats.revealed }} revealed</span>
          <span v-if="questionStats.awaiting" class="stats-pill bg-verse-rose/10 text-verse-rose">{{ questionStats.awaiting }} awaiting</span>
        </div>
      </NuxtLink>

      <NuxtLink to="/roadmap" class="bg-white rounded-xl border border-verse-slate/10 p-4 hover:shadow-md transition">
        <p class="text-xs text-verse-text/50 mb-1">Milestones</p>
        <p class="text-2xl font-serif text-verse-text">{{ milestoneStats.total }}</p>
        <div class="flex gap-2 mt-2">
          <span class="stats-pill bg-green-500/10 text-green-600">{{ milestoneStats.completed }} done</span>
          <span v-if="milestoneStats.confirmed" class="stats-pill bg-verse-gold/10 text-verse-gold">{{ milestoneStats.confirmed }} confirmed</span>
        </div>
      </NuxtLink>
    </div>

    <!-- Quick actions -->
    <div class="flex flex-col sm:flex-row gap-2 mb-8">
      <NuxtLink to="/ledger?new=1" class="flex-1 py-2.5 text-center text-sm rounded-lg border border-verse-slate/20 text-verse-slate hover:bg-verse-slate/5 transition">
        + Propose a Rule
      </NuxtLink>
      <NuxtLink to="/inquiry?new=1" class="flex-1 py-2.5 text-center text-sm rounded-lg border border-verse-slate/20 text-verse-slate hover:bg-verse-slate/5 transition">
        + Ask a Question
      </NuxtLink>
      <NuxtLink to="/roadmap?new=1" class="flex-1 py-2.5 text-center text-sm rounded-lg border border-verse-slate/20 text-verse-slate hover:bg-verse-slate/5 transition">
        + Add Milestone
      </NuxtLink>
    </div>

    <!-- Activity feed -->
    <div>
      <h2 class="text-lg font-serif text-verse-text mb-1">Recent Activity</h2>
      <div class="header-gradient-line w-10 mb-4" />

      <div v-if="activities.length" class="bg-white rounded-xl border border-verse-slate/10 divide-y divide-verse-slate/5">
        <div v-for="(a, i) in activities" :key="i" class="flex items-start gap-3 px-4 py-3">
          <span class="w-2 h-2 rounded-full mt-1.5 shrink-0" :class="activityIcon(a.type)" />
          <div class="flex-1 min-w-0">
            <p class="text-sm text-verse-text">
              <span class="font-medium">{{ a.actor }}</span>
              {{ a.summary.replace(a.actor, '').trim() }}
            </p>
          </div>
          <span class="text-xs text-verse-text/30 shrink-0">{{ relativeTime(a.timestamp) }}</span>
        </div>
      </div>

      <div v-else class="bg-white rounded-xl border border-verse-slate/10 p-8 text-center">
        <p class="text-verse-text/40">No activity yet. Start your journey together.</p>
      </div>
    </div>

    <!-- Geometric divider -->
    <div class="flex justify-center mt-8 gap-2">
      <span class="w-1 h-1 rounded-full bg-verse-slate/15" />
      <span class="w-1.5 h-1.5 rounded-full bg-verse-slate/20" />
      <span class="w-1 h-1 rounded-full bg-verse-slate/15" />
    </div>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

```bash
cd /home/seratusjuta/verses/frontend && npx nuxt build 2>&1 | tail -10
```

- [ ] **Step 3: Commit**

```bash
cd /home/seratusjuta/verses && git add frontend/ && git commit -m "feat(frontend): dashboard page with activity feed and quick stats"
```

---

## Task 5: Frontend Ledger Table View

**Files:**
- Rewrite: `frontend/app/pages/ledger.vue`
- Delete: `frontend/app/components/RuleCard.vue`

- [ ] **Step 1: Delete RuleCard.vue**

```bash
rm /home/seratusjuta/verses/frontend/app/components/RuleCard.vue
```

- [ ] **Step 2: Replace ledger.vue with table view**

Replace `frontend/app/pages/ledger.vue` with:

```vue
<script setup lang="ts">
interface Rule {
  id: number
  title: string
  description: string
  proposed_by: number
  proposer_name: string
  is_sealed: boolean
  is_agreed_by_me: boolean
  is_agreed_by_partner: boolean
  created_at: string
}

const { user } = useAuth()
const { api } = useApi()
const route = useRoute()
const rules = ref<Rule[]>([])
const filter = ref<'all' | 'pending' | 'sealed'>('all')
const showNewForm = ref(false)
const newTitle = ref('')
const newDesc = ref('')
const showOverrideModal = ref(false)
const pendingAction = ref<(() => Promise<void>) | null>(null)
const expandedId = ref<number | null>(null)

async function loadRules() {
  rules.value = await api<Rule[]>('/rules')
}

const filteredRules = computed(() => {
  switch (filter.value) {
    case 'pending':
      return rules.value.filter(r => !r.is_agreed_by_me && !r.is_sealed)
    case 'sealed':
      return rules.value.filter(r => r.is_sealed)
    default:
      return rules.value
  }
})

const stats = computed(() => ({
  total: rules.value.length,
  sealed: rules.value.filter(r => r.is_sealed).length,
  pending: rules.value.filter(r => !r.is_agreed_by_me && !r.is_sealed).length,
}))

function actionLabel(rule: Rule): { text: string; style: string } {
  if (rule.is_sealed) return { text: 'Sealed', style: 'bg-verse-gold text-white' }
  if (rule.is_agreed_by_me && !rule.is_agreed_by_partner) return { text: 'Awaiting partner', style: 'text-verse-text/40' }
  if (!rule.is_agreed_by_me) return { text: 'Sign', style: 'bg-verse-slate text-white cursor-pointer hover:bg-verse-slate/90' }
  return { text: '-', style: 'text-verse-text/20' }
}

function proposerInitial(rule: Rule): string {
  return rule.proposer_name[0]
}

function proposerColor(rule: Rule): string {
  return rule.proposed_by === user.value?.id
    ? (user.value?.username === 'alif' ? 'bg-verse-slate' : 'bg-verse-rose')
    : (user.value?.username === 'alif' ? 'bg-verse-rose' : 'bg-verse-slate')
}

async function createRule(emergencyOverride = false) {
  try {
    await api('/rules', {
      method: 'POST',
      body: { title: newTitle.value, description: newDesc.value, emergency_override: emergencyOverride },
    })
    newTitle.value = ''
    newDesc.value = ''
    showNewForm.value = false
    await loadRules()
  } catch (error: any) {
    if (error?.status === 403 || error?.statusCode === 403) {
      pendingAction.value = () => createRule(true)
      showOverrideModal.value = true
      return
    }
    throw error
  }
}

async function signRule(rule: Rule) {
  if (rule.is_agreed_by_me || rule.is_sealed) return
  await api(`/rules/${rule.id}/sign`, { method: 'POST' })
  await loadRules()
}

async function deleteRule(ruleId: number) {
  await api(`/rules/${ruleId}`, { method: 'DELETE' })
  await loadRules()
}

async function handleOverrideConfirm() {
  showOverrideModal.value = false
  if (pendingAction.value) {
    await pendingAction.value()
    pendingAction.value = null
  }
}

onMounted(() => {
  loadRules()
  if (route.query.new === '1') showNewForm.value = true
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-2 gap-3">
      <div>
        <h1 class="text-2xl font-serif text-verse-text">Distancing Ledger</h1>
        <div class="header-gradient-line w-12" />
        <p class="text-sm text-verse-text/50 mt-2">Seal and sign your shared agreements</p>
      </div>
      <button
        @click="showNewForm = !showNewForm"
        class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition w-full sm:w-auto"
      >
        {{ showNewForm ? 'Cancel' : '+ New Rule' }}
      </button>
    </div>

    <!-- Stats banner -->
    <div class="flex gap-2 mb-4 flex-wrap">
      <span class="stats-pill bg-verse-slate/10 text-verse-text/60">{{ stats.total }} total</span>
      <span class="stats-pill bg-verse-gold/10 text-verse-gold">{{ stats.sealed }} sealed</span>
      <span v-if="stats.pending" class="stats-pill bg-verse-rose/10 text-verse-rose">{{ stats.pending }} pending</span>
    </div>

    <!-- New rule form -->
    <form v-if="showNewForm" @submit.prevent="() => createRule()" class="bg-white rounded-xl border border-verse-slate/10 p-4 sm:p-5 mb-6">
      <input v-model="newTitle" placeholder="Rule title" required class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 text-sm" />
      <textarea v-model="newDesc" placeholder="Describe the rule..." required rows="3" class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none text-sm" />
      <button type="submit" class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">
        Propose Rule
      </button>
    </form>

    <!-- Filter tabs with counts -->
    <div class="flex gap-1 mb-4 bg-white rounded-lg p-1 border border-verse-slate/10 w-full sm:w-fit overflow-x-auto">
      <button
        v-for="f in (['all', 'pending', 'sealed'] as const)"
        :key="f"
        @click="filter = f"
        class="flex-1 sm:flex-none px-3 py-1 text-sm rounded-md transition whitespace-nowrap"
        :class="filter === f ? 'bg-verse-slate text-white' : 'text-verse-text/60 hover:bg-verse-slate/5'"
      >
        {{ f === 'pending' ? 'Pending' : f.charAt(0).toUpperCase() + f.slice(1) }}
        <span class="ml-1 opacity-70">({{ f === 'all' ? stats.total : f === 'pending' ? stats.pending : stats.sealed }})</span>
      </button>
    </div>

    <!-- Table (desktop) -->
    <div class="hidden sm:block bg-white rounded-xl border border-verse-slate/10 overflow-hidden">
      <!-- Header -->
      <div class="grid grid-cols-[2rem_1fr_6rem_2.5rem_2.5rem_8rem] gap-3 px-4 py-2.5 bg-verse-slate/[0.04] text-xs text-verse-text/50 font-medium uppercase tracking-wide border-b border-verse-slate/5">
        <div></div>
        <div>Rule</div>
        <div>By</div>
        <div class="text-center">Me</div>
        <div class="text-center">Partner</div>
        <div class="text-right">Action</div>
      </div>
      <!-- Rows -->
      <div
        v-for="rule in filteredRules"
        :key="rule.id"
        class="grid grid-cols-[2rem_1fr_6rem_2.5rem_2.5rem_8rem] gap-3 px-4 py-3 items-center border-b border-verse-slate/5 last:border-b-0 transition hover:bg-verse-slate/[0.02]"
        :class="rule.is_sealed ? 'bg-verse-gold-light/50' : ''"
      >
        <!-- Status dot -->
        <div class="flex justify-center">
          <span class="w-2.5 h-2.5 rounded-full" :class="rule.is_sealed ? 'bg-verse-gold' : rule.is_agreed_by_me ? 'bg-green-400' : 'bg-verse-slate/20'" />
        </div>
        <!-- Rule info -->
        <div class="min-w-0">
          <p class="text-sm font-medium text-verse-text truncate">{{ rule.title }}</p>
          <p class="text-xs text-verse-text/40 truncate">{{ rule.description }}</p>
        </div>
        <!-- Proposer -->
        <div class="flex items-center gap-1.5">
          <span class="avatar-dot" :class="proposerColor(rule)">{{ proposerInitial(rule) }}</span>
          <span class="text-xs text-verse-text/50 truncate">{{ rule.proposer_name }}</span>
        </div>
        <!-- My signature -->
        <div class="text-center">
          <span v-if="rule.is_agreed_by_me" class="text-green-500 text-sm">&#10003;</span>
          <span v-else class="w-3.5 h-3.5 rounded-full border border-verse-slate/20 inline-block" />
        </div>
        <!-- Partner signature -->
        <div class="text-center">
          <span v-if="rule.is_agreed_by_partner" class="text-green-500 text-sm">&#10003;</span>
          <span v-else class="w-3.5 h-3.5 rounded-full border border-verse-slate/20 inline-block" />
        </div>
        <!-- Action -->
        <div class="flex items-center justify-end gap-2">
          <span
            class="text-xs px-3 py-1 rounded-full font-medium"
            :class="actionLabel(rule).style"
            @click="actionLabel(rule).text === 'Sign' && signRule(rule)"
          >
            {{ actionLabel(rule).text }}
          </span>
          <button
            v-if="rule.proposed_by === user?.id && !rule.is_sealed"
            @click="deleteRule(rule.id)"
            class="text-verse-text/20 hover:text-red-400 transition text-sm"
            title="Delete"
          >
            &times;
          </button>
        </div>
      </div>
      <!-- Empty state -->
      <div v-if="filteredRules.length === 0" class="px-4 py-8 text-center text-verse-text/40">
        No rules match this filter.
      </div>
    </div>

    <!-- Mobile list -->
    <div class="sm:hidden space-y-2">
      <div
        v-for="rule in filteredRules"
        :key="rule.id"
        class="rounded-xl border p-3 transition"
        :class="rule.is_sealed ? 'bg-verse-gold-light/50 border-verse-gold/20' : 'bg-white border-verse-slate/10'"
        @click="expandedId = expandedId === rule.id ? null : rule.id"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2 min-w-0 flex-1">
            <span class="w-2 h-2 rounded-full shrink-0" :class="rule.is_sealed ? 'bg-verse-gold' : rule.is_agreed_by_me ? 'bg-green-400' : 'bg-verse-slate/20'" />
            <span class="text-sm font-medium text-verse-text truncate">{{ rule.title }}</span>
          </div>
          <span
            class="text-xs px-2.5 py-1 rounded-full font-medium shrink-0"
            :class="actionLabel(rule).style"
            @click.stop="actionLabel(rule).text === 'Sign' && signRule(rule)"
          >
            {{ actionLabel(rule).text }}
          </span>
        </div>
        <!-- Expanded detail -->
        <div v-if="expandedId === rule.id" class="mt-3 pt-3 border-t border-verse-slate/5">
          <p class="text-xs text-verse-text/60 mb-2">{{ rule.description }}</p>
          <div class="flex items-center gap-3 text-xs text-verse-text/40">
            <span class="flex items-center gap-1">
              <span class="avatar-dot text-[7px]" :class="proposerColor(rule)">{{ proposerInitial(rule) }}</span>
              {{ rule.proposer_name }}
            </span>
            <span class="flex items-center gap-1">
              <span v-if="rule.is_agreed_by_me" class="text-green-500">&#10003;</span>
              <span v-else class="w-3 h-3 rounded-full border border-verse-slate/20 inline-block" />
              Me
            </span>
            <span class="flex items-center gap-1">
              <span v-if="rule.is_agreed_by_partner" class="text-green-500">&#10003;</span>
              <span v-else class="w-3 h-3 rounded-full border border-verse-slate/20 inline-block" />
              Partner
            </span>
          </div>
          <button
            v-if="rule.proposed_by === user?.id && !rule.is_sealed"
            @click.stop="deleteRule(rule.id)"
            class="text-xs text-red-400 mt-2"
          >
            Delete rule
          </button>
        </div>
      </div>
      <p v-if="filteredRules.length === 0" class="text-center text-verse-text/40 py-8">
        No rules match this filter.
      </p>
    </div>

    <EmergencyOverrideModal
      v-if="showOverrideModal"
      @confirm="handleOverrideConfirm"
      @cancel="showOverrideModal = false; pendingAction = null"
    />
  </div>
</template>
```

- [ ] **Step 3: Verify build**

```bash
cd /home/seratusjuta/verses/frontend && npx nuxt build 2>&1 | tail -10
```

- [ ] **Step 4: Commit**

```bash
cd /home/seratusjuta/verses && git add frontend/ && git commit -m "feat(frontend): ledger table view with expandable mobile rows"
```

---

## Task 6: Frontend Inquiry + Roadmap Visual Enhancement

**Files:**
- Modify: `frontend/app/components/QuestionCard.vue`
- Modify: `frontend/app/pages/inquiry.vue`
- Modify: `frontend/app/components/MilestoneCard.vue`
- Modify: `frontend/app/pages/roadmap.vue`

- [ ] **Step 1: Replace QuestionCard.vue with enhanced version**

```vue
<script setup lang="ts">
interface Answer {
  id: number
  user_id: number
  username: string
  text: string
  created_at: string
}

interface Question {
  id: number
  text: string
  asked_by: number
  asker_name: string
  my_answer: Answer | null
  partner_answer: Answer | null
  created_at: string
}

const props = defineProps<{ question: Question }>()
const emit = defineEmits<{ answer: [questionId: number, text: string] }>()

const { user } = useAuth()
const answerText = ref('')
const showAnswerForm = ref(false)

const partnerName = computed(() => user.value?.partner?.display_name ?? 'Partner')
const hasMyAnswer = computed(() => !!props.question.my_answer)
const hasPartnerAnswer = computed(() => !!props.question.partner_answer)
const bothAnswered = computed(() => hasMyAnswer.value && hasPartnerAnswer.value)

const askerColor = computed(() => {
  if (props.question.asked_by === user.value?.id) {
    return user.value?.username === 'alif' ? 'border-l-verse-slate' : 'border-l-verse-rose'
  }
  return user.value?.username === 'alif' ? 'border-l-verse-rose' : 'border-l-verse-slate'
})

const askerInitial = computed(() => props.question.asker_name[0])
const askerAvatarColor = computed(() => {
  if (props.question.asked_by === user.value?.id) {
    return user.value?.username === 'alif' ? 'bg-verse-slate' : 'bg-verse-rose'
  }
  return user.value?.username === 'alif' ? 'bg-verse-rose' : 'bg-verse-slate'
})

function submitAnswer() {
  if (!answerText.value.trim()) return
  emit('answer', props.question.id, answerText.value)
  answerText.value = ''
  showAnswerForm.value = false
}
</script>

<template>
  <div
    class="bg-white rounded-xl border border-verse-slate/10 p-4 sm:p-5 border-l-[3px] hover:shadow-md transition"
    :class="askerColor"
  >
    <div class="flex items-start justify-between mb-3 gap-2">
      <div class="min-w-0 flex-1">
        <h3 class="font-serif text-base sm:text-lg text-verse-text">{{ question.text }}</h3>
        <div class="flex items-center gap-1.5 mt-1.5">
          <span class="avatar-dot" :class="askerAvatarColor">{{ askerInitial }}</span>
          <span class="text-xs text-verse-text/40">{{ question.asker_name }}</span>
        </div>
      </div>
      <span
        v-if="bothAnswered"
        class="text-xs px-2 py-0.5 rounded-full bg-verse-gold text-white font-medium shrink-0"
      >
        Revealed
      </span>
    </div>

    <div class="space-y-3 mt-4">
      <!-- My answer -->
      <div v-if="hasMyAnswer" class="rounded-lg p-3 bg-verse-slate/5 border-l-[3px] border-l-verse-slate">
        <p class="text-xs font-medium text-verse-slate mb-1">Your answer</p>
        <p class="text-sm text-verse-text">{{ question.my_answer!.text }}</p>
      </div>

      <!-- Partner answer - revealed or hidden -->
      <div v-if="bothAnswered" class="rounded-lg p-3 bg-verse-rose/5 border-l-[3px] border-l-verse-rose">
        <p class="text-xs font-medium text-verse-rose mb-1">{{ partnerName }}'s answer</p>
        <p class="text-sm text-verse-text">{{ question.partner_answer!.text }}</p>
      </div>
      <MountainBackground v-else-if="!hasMyAnswer" />

      <!-- Answer button / form -->
      <div v-if="!hasMyAnswer">
        <button
          v-if="!showAnswerForm"
          @click="showAnswerForm = true"
          class="w-full py-2.5 text-sm rounded-lg border border-verse-slate/20 text-verse-slate hover:bg-verse-slate/5 transition animate-soft-pulse"
        >
          Write your answer
        </button>
        <form v-else @submit.prevent="submitAnswer" class="space-y-2">
          <textarea
            v-model="answerText"
            rows="3"
            placeholder="Share your thoughts..."
            class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none text-sm"
          />
          <div class="flex gap-2">
            <button type="submit" class="px-4 py-1.5 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">
              Submit
            </button>
            <button type="button" @click="showAnswerForm = false" class="px-4 py-1.5 text-sm text-verse-text/50 hover:text-verse-text transition">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Replace inquiry.vue with enhanced version**

```vue
<script setup lang="ts">
interface Answer {
  id: number
  user_id: number
  username: string
  text: string
  created_at: string
}

interface Question {
  id: number
  text: string
  asked_by: number
  asker_name: string
  my_answer: Answer | null
  partner_answer: Answer | null
  created_at: string
}

const { api } = useApi()
const route = useRoute()
const questions = ref<Question[]>([])
const showNewForm = ref(false)
const newText = ref('')
const showOverrideModal = ref(false)
const pendingAction = ref<(() => Promise<void>) | null>(null)

async function loadQuestions() {
  questions.value = await api<Question[]>('/questions')
}

const stats = computed(() => ({
  total: questions.value.length,
  revealed: questions.value.filter(q => q.my_answer && q.partner_answer).length,
  awaiting: questions.value.filter(q => !q.my_answer).length,
}))

async function createQuestion(emergencyOverride = false) {
  try {
    await api('/questions', {
      method: 'POST',
      body: { text: newText.value, emergency_override: emergencyOverride },
    })
    newText.value = ''
    showNewForm.value = false
    await loadQuestions()
  } catch (error: any) {
    if (error?.status === 403 || error?.statusCode === 403) {
      pendingAction.value = () => createQuestion(true)
      showOverrideModal.value = true
      return
    }
    throw error
  }
}

async function answerQuestion(questionId: number, text: string, emergencyOverride = false) {
  try {
    await api(`/questions/${questionId}/answer`, {
      method: 'POST',
      body: { text, emergency_override: emergencyOverride },
    })
    await loadQuestions()
  } catch (error: any) {
    if (error?.status === 403 || error?.statusCode === 403) {
      pendingAction.value = () => answerQuestion(questionId, text, true)
      showOverrideModal.value = true
      return
    }
    throw error
  }
}

async function handleOverrideConfirm() {
  showOverrideModal.value = false
  if (pendingAction.value) {
    await pendingAction.value()
    pendingAction.value = null
  }
}

onMounted(() => {
  loadQuestions()
  if (route.query.new === '1') showNewForm.value = true
})
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-2 gap-3">
      <div>
        <h1 class="text-2xl font-serif text-verse-text">Inquiry Hub</h1>
        <div class="header-gradient-line w-10" />
        <p class="text-sm text-verse-text/50 mt-2">Ask, reflect, then reveal together</p>
      </div>
      <button
        @click="showNewForm = !showNewForm"
        class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition w-full sm:w-auto"
      >
        {{ showNewForm ? 'Cancel' : '+ New Question' }}
      </button>
    </div>

    <!-- Stats banner -->
    <div class="flex gap-2 mb-4 flex-wrap">
      <span class="stats-pill bg-verse-slate/10 text-verse-text/60">{{ stats.total }} total</span>
      <span class="stats-pill bg-verse-gold/10 text-verse-gold">{{ stats.revealed }} revealed</span>
      <span v-if="stats.awaiting" class="stats-pill bg-verse-rose/10 text-verse-rose">{{ stats.awaiting }} awaiting</span>
    </div>

    <form v-if="showNewForm" @submit.prevent="() => createQuestion()" class="bg-white rounded-xl border border-verse-slate/10 p-4 sm:p-5 mb-6">
      <textarea
        v-model="newText"
        placeholder="What would you like to explore together?"
        required
        rows="3"
        class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none text-sm"
      />
      <button type="submit" class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">
        Ask Question
      </button>
    </form>

    <div class="space-y-4">
      <QuestionCard
        v-for="q in questions"
        :key="q.id"
        :question="q"
        @answer="answerQuestion"
      />
      <p v-if="questions.length === 0" class="text-center text-verse-text/40 py-8">
        No questions yet. Start exploring together.
      </p>
    </div>

    <EmergencyOverrideModal
      v-if="showOverrideModal"
      @confirm="handleOverrideConfirm"
      @cancel="showOverrideModal = false; pendingAction = null"
    />
  </div>
</template>
```

- [ ] **Step 3: Replace MilestoneCard.vue with enhanced version**

```vue
<script setup lang="ts">
interface Milestone {
  id: number
  title: string
  description: string
  target_date: string | null
  proposed_by: number
  proposer_name: string
  is_confirmed: boolean
  is_completed: boolean
  is_approved_by_me: boolean
  is_approved_by_partner: boolean
  created_at: string
}

const props = defineProps<{ milestone: Milestone; isLast?: boolean }>()
const emit = defineEmits<{
  approve: [milestoneId: number]
  complete: [milestoneId: number]
  delete: [milestoneId: number]
}>()

const { user } = useAuth()
const isMyProposal = computed(() => props.milestone.proposed_by === user.value?.id)

const statusLabel = computed(() => {
  if (props.milestone.is_completed) return 'Completed'
  if (props.milestone.is_confirmed) return 'Confirmed'
  return 'Proposed'
})

const statusColor = computed(() => {
  if (props.milestone.is_completed) return 'bg-green-500'
  if (props.milestone.is_confirmed) return 'bg-verse-gold'
  return 'bg-verse-slate/30'
})

const lineGradient = computed(() => {
  if (props.milestone.is_completed) return 'from-green-500/30 to-verse-gold/20'
  if (props.milestone.is_confirmed) return 'from-verse-gold/30 to-verse-slate/10'
  return 'from-verse-slate/15 to-verse-slate/5'
})

const proposerColor = computed(() => {
  if (props.milestone.proposed_by === user.value?.id) {
    return user.value?.username === 'alif' ? 'bg-verse-slate' : 'bg-verse-rose'
  }
  return user.value?.username === 'alif' ? 'bg-verse-rose' : 'bg-verse-slate'
})

const cardBorderColor = computed(() => {
  if (props.milestone.proposed_by === user.value?.id) {
    return user.value?.username === 'alif' ? 'border-l-verse-slate' : 'border-l-verse-rose'
  }
  return user.value?.username === 'alif' ? 'border-l-verse-rose' : 'border-l-verse-slate'
})

function formatDate(d: string | null) {
  if (!d) return null
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<template>
  <div class="flex gap-3 sm:gap-4">
    <!-- Timeline line + dot -->
    <div class="flex flex-col items-center shrink-0">
      <div
        class="w-4 h-4 rounded-full mt-1 flex items-center justify-center text-white text-[8px]"
        :class="statusColor"
      >
        <span v-if="milestone.is_completed">&#10003;</span>
      </div>
      <div
        v-if="!isLast"
        class="w-0.5 flex-1 mt-1 bg-gradient-to-b"
        :class="lineGradient"
      />
    </div>

    <!-- Card -->
    <div
      class="flex-1 rounded-xl border p-4 sm:p-5 mb-4 transition min-w-0 border-l-[3px] hover:shadow-md"
      :class="[
        milestone.is_confirmed ? 'bg-verse-gold-light/50 border-verse-gold/20' : 'bg-white border-verse-slate/10',
        cardBorderColor
      ]"
    >
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1 flex-wrap">
            <h3 class="font-serif text-base sm:text-lg text-verse-text">{{ milestone.title }}</h3>
            <span class="text-xs px-2 py-0.5 rounded-full text-white font-medium shrink-0" :class="statusColor">
              {{ statusLabel }}
            </span>
          </div>
          <p class="text-sm text-verse-text/70">{{ milestone.description }}</p>
          <p v-if="milestone.target_date" class="text-xs text-verse-text/40 mt-2">
            Target: {{ formatDate(milestone.target_date) }}
          </p>
        </div>

        <button
          v-if="isMyProposal && !milestone.is_confirmed"
          @click="emit('delete', milestone.id)"
          class="text-verse-text/30 hover:text-red-400 transition text-lg shrink-0"
          title="Delete milestone"
        >
          &times;
        </button>
      </div>

      <div class="mt-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div class="flex items-center gap-3 text-xs text-verse-text/50 flex-wrap">
          <span class="flex items-center gap-1.5">
            <span class="avatar-dot" :class="proposerColor">{{ milestone.proposer_name[0] }}</span>
            {{ milestone.proposer_name }}
          </span>
          <span class="flex items-center gap-1">
            <span v-if="milestone.is_approved_by_me" class="text-green-500 text-sm">&#10003;</span>
            <span v-else class="w-3.5 h-3.5 rounded-full border border-verse-slate/20 inline-block" />
            Me
          </span>
          <span class="flex items-center gap-1">
            <span v-if="milestone.is_approved_by_partner" class="text-green-500 text-sm">&#10003;</span>
            <span v-else class="w-3.5 h-3.5 rounded-full border border-verse-slate/20 inline-block" />
            Partner
          </span>
        </div>

        <div class="flex gap-2 w-full sm:w-auto">
          <button
            v-if="!milestone.is_approved_by_me && !milestone.is_completed"
            @click="emit('approve', milestone.id)"
            class="flex-1 sm:flex-none px-3 py-1.5 text-sm rounded-lg bg-verse-slate text-white hover:bg-verse-slate/90 transition"
          >
            Approve
          </button>
          <button
            v-if="milestone.is_confirmed && !milestone.is_completed"
            @click="emit('complete', milestone.id)"
            class="flex-1 sm:flex-none px-3 py-1.5 text-sm rounded-lg bg-green-500 text-white hover:bg-green-600 transition"
          >
            Complete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 4: Replace roadmap.vue with enhanced version**

```vue
<script setup lang="ts">
interface Milestone {
  id: number
  title: string
  description: string
  target_date: string | null
  proposed_by: number
  proposer_name: string
  is_confirmed: boolean
  is_completed: boolean
  is_approved_by_me: boolean
  is_approved_by_partner: boolean
  created_at: string
}

const { api } = useApi()
const route = useRoute()
const milestones = ref<Milestone[]>([])
const showNewForm = ref(false)
const newTitle = ref('')
const newDesc = ref('')
const newDate = ref('')

async function loadMilestones() {
  milestones.value = await api<Milestone[]>('/milestones')
}

const stats = computed(() => {
  const completed = milestones.value.filter(m => m.is_completed).length
  const confirmed = milestones.value.filter(m => m.is_confirmed && !m.is_completed).length
  const proposed = milestones.value.filter(m => !m.is_confirmed).length
  const total = milestones.value.length
  const progress = total > 0 ? Math.round((completed / total) * 100) : 0
  return { completed, confirmed, proposed, total, progress }
})

async function createMilestone() {
  await api('/milestones', {
    method: 'POST',
    body: {
      title: newTitle.value,
      description: newDesc.value,
      target_date: newDate.value || null,
    },
  })
  newTitle.value = ''
  newDesc.value = ''
  newDate.value = ''
  showNewForm.value = false
  await loadMilestones()
}

async function approveMilestone(id: number) {
  await api(`/milestones/${id}/approve`, { method: 'POST' })
  await loadMilestones()
}

async function completeMilestone(id: number) {
  await api(`/milestones/${id}`, { method: 'PATCH', body: { is_completed: true } })
  await loadMilestones()
}

async function deleteMilestone(id: number) {
  await api(`/milestones/${id}`, { method: 'DELETE' })
  await loadMilestones()
}

onMounted(() => {
  loadMilestones()
  if (route.query.new === '1') showNewForm.value = true
})
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-2 gap-3">
      <div>
        <h1 class="text-2xl font-serif text-verse-text">Marriage Roadmap</h1>
        <div class="header-gradient-line w-14" />
        <p class="text-sm text-verse-text/50 mt-2">Your journey together, one milestone at a time</p>
      </div>
      <button
        @click="showNewForm = !showNewForm"
        class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition w-full sm:w-auto"
      >
        {{ showNewForm ? 'Cancel' : '+ Propose Milestone' }}
      </button>
    </div>

    <!-- Stats + progress bar -->
    <div class="mb-4">
      <div class="flex gap-2 mb-2 flex-wrap">
        <span class="stats-pill bg-verse-slate/10 text-verse-text/60">{{ stats.total }} total</span>
        <span class="stats-pill bg-green-500/10 text-green-600">{{ stats.completed }} completed</span>
        <span class="stats-pill bg-verse-gold/10 text-verse-gold">{{ stats.confirmed }} confirmed</span>
        <span v-if="stats.proposed" class="stats-pill bg-verse-slate/10 text-verse-slate">{{ stats.proposed }} proposed</span>
      </div>
      <div v-if="stats.total > 0" class="h-1.5 bg-verse-slate/10 rounded-full overflow-hidden">
        <div
          class="h-full bg-gradient-to-r from-verse-gold to-green-500 rounded-full transition-all duration-500"
          :style="{ width: stats.progress + '%' }"
        />
      </div>
      <p v-if="stats.total > 0" class="text-xs text-verse-text/40 mt-1">{{ stats.completed }} of {{ stats.total }} milestones completed</p>
    </div>

    <form v-if="showNewForm" @submit.prevent="createMilestone" class="bg-white rounded-xl border border-verse-slate/10 p-4 sm:p-5 mb-6">
      <input v-model="newTitle" placeholder="Milestone title" required class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 text-sm" />
      <textarea v-model="newDesc" placeholder="Describe this milestone..." required rows="3" class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 resize-none text-sm" />
      <input v-model="newDate" type="date" class="w-full px-3 py-2 rounded-lg border border-verse-slate/20 mb-3 focus:outline-none focus:ring-2 focus:ring-verse-slate/30 text-sm" />
      <button type="submit" class="px-4 py-2 bg-verse-slate text-white text-sm rounded-lg hover:bg-verse-slate/90 transition">
        Propose
      </button>
    </form>

    <div>
      <MilestoneCard
        v-for="(m, i) in milestones"
        :key="m.id"
        :milestone="m"
        :is-last="i === milestones.length - 1"
        @approve="approveMilestone"
        @complete="completeMilestone"
        @delete="deleteMilestone"
      />
      <p v-if="milestones.length === 0" class="text-center text-verse-text/40 py-8">
        No milestones yet. Propose your first step forward.
      </p>
    </div>
  </div>
</template>
```

- [ ] **Step 5: Verify build**

```bash
cd /home/seratusjuta/verses/frontend && npx nuxt build 2>&1 | tail -10
```

- [ ] **Step 6: Commit**

```bash
cd /home/seratusjuta/verses && git add frontend/ && git commit -m "feat(frontend): visual enhancement for inquiry and roadmap pages"
```

---

## Task 7: Final Integration Test

- [ ] **Step 1: Run all backend tests**

```bash
cd /home/seratusjuta/verses/backend && source venv/bin/activate && pytest -v
```

Expected: All 34 tests pass.

- [ ] **Step 2: Verify frontend builds**

```bash
cd /home/seratusjuta/verses/frontend && npx nuxt build 2>&1 | tail -10
```

Expected: Build complete.

- [ ] **Step 3: Report results**
