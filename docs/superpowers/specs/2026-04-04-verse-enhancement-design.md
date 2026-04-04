# Verse UI Enhancement & Auto-Approve Design Spec

## Overview

Enhance the Verse application with richer visual design, auto-approve logic for proposers, a global activity feed, and a redesigned Ledger table view. The app currently feels too sparse and empty — this update adds visual texture, information density, and a dashboard landing page.

## 1. Backend: Auto-Approve for Proposer

When a user creates a rule or milestone, they automatically receive a signature/approval record.

**Rules (`POST /rules`):**
- After creating the rule, automatically insert a `RuleSignature` for the proposer
- If partner then signs, the rule becomes sealed (2 signatures)
- Proposer never sees a "Sign" button on their own rules

**Milestones (`POST /milestones`):**
- After creating the milestone, automatically insert a `MilestoneApproval` for the proposer
- If partner then approves, the milestone becomes confirmed (2 approvals)
- Proposer never sees an "Approve" button on their own milestones

## 2. Backend: Activity Feed Endpoint

**`GET /activity`** — returns the last 20 actions across all modules, ordered by most recent.

Response schema:
```json
[
  {
    "type": "rule_sealed",
    "actor": "Syifa",
    "summary": "Rule \"No late calls\" has been sealed",
    "timestamp": "2026-04-03T14:30:00"
  }
]
```

**Event types and sources:**
- `rule_created` — from `rules.created_at`, actor = proposer
- `rule_signed` — from `rule_signatures.signed_at`, actor = signer (exclude auto-sign by proposer)
- `rule_sealed` — from `rule_signatures.signed_at` where the sign caused `is_sealed=True`, summary mentions the rule is sealed
- `question_asked` — from `questions.created_at`, actor = asker
- `answer_submitted` — from `answers.created_at`, actor = answerer
- `answers_revealed` — when both answers exist for a question, timestamp = the later answer's `created_at`
- `milestone_proposed` — from `milestones.created_at`, actor = proposer
- `milestone_approved` — from `milestone_approvals.approved_at`, actor = approver (exclude auto-approve by proposer)
- `milestone_confirmed` — from `milestone_approvals.approved_at` where approval caused `is_confirmed=True`
- `milestone_completed` — from milestones where `is_completed=True`, use `created_at` of the update (we don't track this separately, so use the latest `milestone_approvals.approved_at` or milestone `created_at` as fallback)

**Implementation:** Query each source table, build a unified list, sort by timestamp desc, limit to 20. No new database table needed.

## 3. Frontend: Dashboard Page (`/`)

Replaces the current index redirect. Becomes the landing page after login.

**Nav update:** Add "Home" as the first nav item (path: `/`). Nav order: Home, Ledger, Inquiry, Roadmap.

**Dashboard layout:**
- **Header area:** "Welcome back, Alif" with partner status ("Syifa is offline")
- **Quick stats row:** 3 pill-shaped badges showing counts:
  - Rules: "3 Sealed / 1 Pending"
  - Questions: "2 Revealed / 1 Awaiting"
  - Milestones: "2 of 5 Completed"
- **Activity feed:** Last 10 items, each with:
  - Type icon (small colored dot or symbol)
  - Actor name in bold
  - Summary text
  - Relative timestamp ("2 days ago", "just now")
  - Styled as a clean list with subtle dividers
- **Quick actions:** 3 buttons in a row: "Propose a Rule", "Ask a Question", "Add Milestone" — each links to the respective page with the form pre-opened (via query param `?new=1`)
- **Decorative:** Topographic background pattern (same as login, 3% opacity)

## 4. Frontend: Ledger Table View

Replace stacked cards with a structured list/table view.

**Desktop (sm and up):**
- Rounded container with subtle border, white background
- **Header row:** light slate background, columns: Status | Rule | Proposed by | Me | Partner | Action
- **Data rows:** each rule is a row with aligned columns
  - Status: small colored dot (gold if sealed, green if signed by me, slate/20 if pending)
  - Rule: title (bold) + description (truncated, muted) in one cell
  - Proposed by: avatar circle (A/S with user color) + name
  - Me: green checkmark if signed, empty circle if not
  - Partner: green checkmark if signed, empty circle if not
  - Action: "Sign" button | "Sealed" gold badge | "Awaiting partner" muted text
- Sealed rows: `bg-verse-gold-light` tint
- Subtle `border-b border-verse-slate/5` between rows (no grid lines)
- Hover: `bg-verse-slate/[0.02]` background shift

**Mobile (below sm):**
- Compact list rows, no table structure
- Each row: left side has status dot + title, right side has action badge/button
- Tap to expand: shows description, proposer, signature status
- Swipe or tap interactions for sign/delete

**Filter tabs** remain above (All / Pending My Signature / Sealed) with stats counts in each tab label: "All (5)" / "Pending (1)" / "Sealed (3)"

## 5. Frontend: Visual Enrichment

### All Pages

**Background texture:**
- Subtle topographic SVG pattern on all page backgrounds at 3% opacity (reuse the login page pattern)
- Applied in the default layout, behind `<slot />`

**Page headers:**
- Decorative gradient underline beneath each page title: thin line, gradient from `verse-slate` to `verse-gold`
- Stats banner directly below the header (see per-page stats below)

**Geometric dividers:**
- Small geometric dot patterns (5 dots in a diamond shape) as section separators where needed

### Cards (Inquiry + Roadmap)

- **Left-border accent:** 3px left border — `verse-slate` for Alif's items, `verse-rose` for Syifa's
- **Hover:** `shadow-md` transition on hover (from current subtle shadow)
- **Avatar indicators:** Replace plain colored dots for "Me/Partner" with small avatar circles showing first letter (A/S) with the user's color background

### Inquiry Page Enhancements

- **Pulsing button:** "Write your answer" button gets a subtle pulse animation (`animate-pulse` but gentler — custom keyframe, opacity 0.7 to 1.0) on unanswered questions to draw attention
- **Revealed answers:** Left accent bar — 3px border-left in `verse-slate` for your answer, `verse-rose` for partner's answer (quote-style)
- **Stats banner:** "2 Revealed / 1 Awaiting Your Answer / 4 Total"

### Roadmap Page Enhancements

- **Timeline gradient:** The vertical line fades from `verse-slate` (top/pending) to `verse-gold` (bottom/completed) based on milestone status
- **Completed dot:** Shows a small checkmark (&#10003;) inside the timeline dot for completed milestones
- **Progress bar:** At the top, below the stats banner: thin horizontal bar showing completion percentage, `verse-gold` fill on `verse-slate/10` track
- **Stats banner:** "1 Completed / 2 Confirmed / 1 Proposed" + progress bar

### Login Page

No changes — already has the richest visual treatment.

### NavBar

- Active nav item gets a subtle bottom border indicator (2px `verse-gold`) in addition to the background highlight
- Partner online status: small green/gray dot next to the user avatar
