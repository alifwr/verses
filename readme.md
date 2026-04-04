The vision for **Verse** has been updated to include a secure authentication layer, ensuring the application remains a private and protected space for the two primary users.

### **Updated Project Summary: Verse**
**Verse** is a collaborative, boundary-management web application designed for a couple to align on their shared future. It digitizes specific relationship rules, facilitates deep inquiry through shared questions, and tracks milestones on a roadmap toward marriage.

* **Core Modules:** * **Distancing Ledger:** A "Seal and Sign" system for relationship rules.
    * **Inquiry Hub:** A double-blind Q&A module for future planning.
    * **Marriage Roadmap:** A vertical timeline for tracking administrative and personal goals.
    * **Auth & Security:** A private, invitation-only authentication system.
* **Design:** A "Misty Mountain" aesthetic blending modern minimalism with subtle religious elements (geometric patterns, serif typography, and topographic lines).
* **Safety Features:** A 10:00 PM digital curfew and an emergency bypass system for essential communication.

---

### **Part 1: Updated Frontend Prompt (Nuxt 4)**

> **Task:** Update the "Verse" frontend using **Nuxt 4** to include a robust authentication and authorization flow.
> 
> **Authentication Requirements:**
> - Implement a dedicated **Login Page** with a minimalist mountain-themed background. 
> - Integrate an authentication library (e.g., **Auth.js** or **Sidebase Nuxt Auth**).
> - Use **Middleware** to protect all core routes (`/ledger`, `/inquiry`, `/roadmap`). Redirect unauthenticated users to the login screen.
> - Display user-specific profiles (Partner 1 and Partner 2) with distinct visual cues.
> 
> **Feature Enhancements:**
> - **The Ledger:** Add a "Pending My Signature" filter. Display "Agreement" status only when the authenticated user’s partner has also signed the rule.
> - **Inquiry Hub:** Ensure the "Double-Blind" reveal logic is strictly enforced in the UI. Answers should remain blurred or hidden with a mountain silhouette placeholder until the current user has submitted their own response.
> - **Roadmap:** Allow both users to propose milestones, with a "Confirmed" state triggered only by mutual approval.
> 
> **UI/UX:**
> - Maintain the "High Grounds" aesthetic: #F5F5F5 background, Slate Blue accents, and Gold for "Sealed" states.
> - Use **Tailwind CSS** for a responsive, mobile-first design.

---

### **Part 2: Updated Backend Prompt (FastAPI)**

> **Task:** Develop the "Verse" backend using **FastAPI** and **PostgreSQL**, incorporating a secure JWT-based authentication system.
> 
> **Security & Auth Logic:**
> - **User Management:** Create a schema for exactly two users. Disable public registration; users must be pre-seeded or invited via a secure, one-time-use token.
> - **JWT Implementation:** Use `OAuth2PasswordBearer` for securing endpoints. Implement token expiration and refresh logic.
> - **Data Access Control:** Ensure every request is validated against the user's ID. Users should only be able to view their partner's answers in the `Inquiry Hub` if they have also provided an answer for that specific record.
> 
> **API Endpoints (Additions):**
> - `POST /auth/login`: Validate credentials and return a JWT access token.
> - `GET /auth/me`: Return current user profile and the status of their partner (online/offline).
> - `GET /rules`: Return rules with specific boolean flags for `is_agreed_by_me` and `is_agreed_by_partner`.
> - `GET /questions/{id}`: Logic gate to hide `partner_answer` unless the requester has a corresponding entry in the `answers` table.
> 
> **The Adab Middleware:**
> - Implement a global dependency that checks the server time. Between 10:00 PM and 4:00 AM, all non-GET requests to the `Ledger` or `Inquiry` modules must return a `403 Forbidden` status unless an `emergency_override` flag is present in the request body.
> 
> **Database Schema Updates:**
> - Add a `users` table with hashed passwords and unique identifiers.
> - Add a `sessions` table to track active connections and curfew status.
> - Update `rules` and `milestones` tables with foreign keys linking to the user who proposed or agreed to them.
