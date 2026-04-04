# Verse - Application Design Spec

## Overview

Verse is a collaborative, boundary-management web application for a couple (Alif and Syifa) to align on their shared future. It digitizes relationship rules, facilitates deep inquiry through shared questions, and tracks milestones on a roadmap toward marriage.

## Architecture

- **Frontend**: Nuxt 4 + Tailwind CSS (in `frontend/`)
- **Backend**: FastAPI + SQLAlchemy + SQLite (in `backend/`)
- **Auth**: Custom JWT-based, no third-party auth library

## Users

Two pre-seeded users: `alif` and `syifa`, default password `verse2024` for both. No public registration. Each user is linked as the other's partner.

## Backend (FastAPI)

### Database Schema (SQLite via SQLAlchemy)

**users**
- `id`: Integer PK
- `username`: String, unique
- `display_name`: String
- `hashed_password`: String
- `partner_id`: Integer FK -> users.id
- `is_online`: Boolean
- `created_at`: DateTime

**sessions**
- `id`: Integer PK
- `user_id`: Integer FK -> users.id
- `token`: String
- `is_active`: Boolean
- `created_at`: DateTime
- `expires_at`: DateTime

**rules**
- `id`: Integer PK
- `title`: String
- `description`: Text
- `proposed_by`: Integer FK -> users.id
- `is_sealed`: Boolean (true when both signed)
- `created_at`: DateTime

**rule_signatures**
- `id`: Integer PK
- `rule_id`: Integer FK -> rules.id
- `user_id`: Integer FK -> users.id
- `signed_at`: DateTime

**questions**
- `id`: Integer PK
- `text`: Text
- `asked_by`: Integer FK -> users.id
- `created_at`: DateTime

**answers**
- `id`: Integer PK
- `question_id`: Integer FK -> questions.id
- `user_id`: Integer FK -> users.id
- `text`: Text
- `created_at`: DateTime

**milestones**
- `id`: Integer PK
- `title`: String
- `description`: Text
- `target_date`: Date (nullable)
- `proposed_by`: Integer FK -> users.id
- `is_confirmed`: Boolean (true when both approved)
- `is_completed`: Boolean
- `created_at`: DateTime

**milestone_approvals**
- `id`: Integer PK
- `milestone_id`: Integer FK -> milestones.id
- `user_id`: Integer FK -> users.id
- `approved_at`: DateTime

### Auth

- `python-jose` for JWT encode/decode
- `passlib` with bcrypt for password hashing
- `OAuth2PasswordBearer` for securing endpoints
- Access token expiry: 30 minutes
- Refresh token expiry: 7 days

### API Endpoints

**Auth**
- `POST /auth/login` - Validate credentials, return JWT access + refresh tokens
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Return current user profile and partner online status

**Rules (Ledger)**
- `GET /rules` - List rules with `is_agreed_by_me` and `is_agreed_by_partner` flags
- `POST /rules` - Create a new rule (proposed by current user)
- `POST /rules/{id}/sign` - Sign/agree to a rule
- `DELETE /rules/{id}` - Delete a rule (only by proposer, only if not sealed)

**Questions (Inquiry Hub)**
- `GET /questions` - List all questions
- `POST /questions` - Create a new question
- `GET /questions/{id}` - Get question detail; hides `partner_answer` unless current user has answered
- `POST /questions/{id}/answer` - Submit answer to a question

**Milestones (Roadmap)**
- `GET /milestones` - List all milestones with approval status
- `POST /milestones` - Propose a new milestone
- `POST /milestones/{id}/approve` - Approve a milestone
- `PATCH /milestones/{id}` - Update milestone (mark complete, edit)
- `DELETE /milestones/{id}` - Delete (only by proposer, only if not confirmed)

### Adab Middleware (Curfew)

Global dependency that checks server time. Between 22:00 and 04:00:
- All non-GET requests to `/rules` and `/questions` endpoints return `403 Forbidden`
- Exception: request body contains `emergency_override: true`
- GET requests always allowed

## Frontend (Nuxt 4)

### Design Tokens

- Background: `#F5F5F5`
- Slate Blue accent: `#6B7FA3`
- Gold (sealed/confirmed states): `#C5A55A`
- Text: `#2D3748` (dark slate)
- Typography: Serif for headings (Playfair Display), sans-serif for body (Inter)
- Subtle topographic line patterns as background decoration
- Geometric Islamic-inspired patterns for borders/dividers

### Pages

**`/login`** - Mountain-themed background, minimalist login form, app name "Verse" in serif
**`/ledger`** - Rule cards with seal/sign interaction, filter tabs (All / Pending My Signature / Sealed)
**`/inquiry`** - Question cards, double-blind answer reveal, mountain silhouette placeholder for hidden answers
**`/roadmap`** - Vertical timeline, milestone cards, propose/approve interactions

### Auth Flow

- `useAuth` composable: manages JWT token in httpOnly cookie, provides `login()`, `logout()`, `user` ref, `isAuthenticated` computed
- `auth.global.ts` middleware: checks auth state on every route change, redirects to `/login` if unauthenticated
- API utility (`useApi`): auto-attaches Authorization header to all requests

### Component Hierarchy

- `AppLayout` - Main layout with nav sidebar/bottom bar, user profile indicator
- `NavBar` - Links to Ledger, Inquiry, Roadmap; shows current user avatar/name
- `RuleCard` - Displays rule with sign button, sealed gold badge
- `QuestionCard` - Shows question, blurred/revealed answer states
- `MilestoneCard` - Timeline node with approve button, confirmed badge
- `MountainBackground` - SVG mountain silhouette for login and placeholders
- `EmergencyOverrideModal` - Modal for curfew bypass

### User-Specific Visual Cues

- Alif: Slate Blue accent on their elements
- Syifa: A complementary muted rose accent (`#B07D8E`)
- Each user sees their partner's items with the partner's color
