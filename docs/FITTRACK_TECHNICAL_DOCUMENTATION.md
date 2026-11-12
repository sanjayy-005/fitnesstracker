# FitTrack – Complete Technical Documentation

**Product:** FitTrack Gym Management System  
**Document type:** Technical handover  
**Codebase:** this repository (`backend/`, `frontend/`)  
**Rule:** only behaviour verified in source is described as implemented. Gaps are labelled.

Related files:

- [FITTRACK_ARCHITECTURE.md](./FITTRACK_ARCHITECTURE.md) — diagrams
- [FITTRACK_DEVELOPER_SETUP.md](./FITTRACK_DEVELOPER_SETUP.md) — local install
- [FITTRACK_API_REFERENCE.md](./FITTRACK_API_REFERENCE.md) — endpoint catalogue
- [FITTRACK_PROJECT_STATUS.md](./FITTRACK_PROJECT_STATUS.md) — implemented vs planned

---

# Chapter 1 – Project Overview

## What FitTrack is

FitTrack is a **web application for a single gym** (the seed data and gym receipt settings assume a Coimbatore-style gym named “FitTrack Gym”). Front-desk staff and admins manage people, memberships, money **records**, and door traffic. Trainers see the members assigned to them. Members can log in to a small self-service area and optionally log meals from photographs.

It is a **portfolio / academic / operations** system: it does not process card payments through a bank, and it does not replace a clinical dietitian.

## Why it was developed

Gyms often track members in spreadsheets or disconnected tools: who paid, whose plan expired, who checked in today. FitTrack puts those workflows in one place with **role-based access**, so a trainer cannot see all revenue, and a member cannot open the staff desk.

## Problems it solves (as implemented)

1. Keep a member directory with codes like `FT00001`.
2. Sell monthly / quarterly / yearly plans and renew without overlapping dates incorrectly.
3. Record cash, UPI, card, or bank-transfer **receipts** and print them.
4. Check members in once per day if they have an active membership.
5. Show a dashboard of counts, expiry risk, attendance, and (for admin/staff) revenue charts.
6. Let a member see their own membership and visits, and estimate meal calories from a photo using a vision language model (or a mock).

## Target users

| User | In the product |
|---|---|
| Gym owner / admin | Full control, user accounts |
| Front desk (`STAFF`) | Day-to-day members, sales, payments, attendance |
| Trainer | Assigned members, check-in, dashboard without finance |
| Member | Portal + food log |

## Main objectives

- Accurate membership dates and expiry (`Membership.effective_status`, `sync_expired`).
- Server-side permissions (`backend/core/permissions.py`), not UI-only hiding.
- Indian-gym-friendly details: INR formatting, UPI, household food units in the nutrition prompt.

## Project scope

**In scope in this repo:** gym CRM-style operations + member portal + optional LLM nutrition.

**Out of scope (not built):** payment gateways, multi-location franchises, native mobile apps, workout programming, QR hardware.

## Key functionalities

Staff: dashboard, members, trainers, plans, memberships, payments, attendance, user accounts (admin).  
Member: home, food log, membership history, visits.  
Shared: JWT login.

---

# Chapter 2 – Technology Stack

Only packages and services referenced by the repo are listed.

## Backend

| Technology | What it is | Why FitTrack uses it | Where |
|---|---|---|---|
| Python | Language | Django ecosystem | `backend/` |
| Django 5.2 | Web framework | ORM, admin, settings, management commands | `requirements.txt` `Django>=5.2,<5.3` |
| Django REST Framework | HTTP API | ViewSets, serializers, permissions | all `views.py` |
| SimpleJWT | JSON Web Tokens | Login without server sessions for the SPA | `djangorestframework-simplejwt`, blacklist app |
| django-cors-headers | CORS | Allow the Vite/Vercel origin to call the API | `CorsMiddleware` |
| django-filter | Query filters | Member status, payments, attendance | `filters.py` modules |
| MySQL 8 | Relational database | Durable gym records | `DB_ENGINE=mysql` |
| PyMySQL | Pure-Python MySQL driver | Installs without compiling `mysqlclient` | `settings.py` `install_as_MySQLdb()` |
| cryptography | TLS extras | Used with PyMySQL SSL options | `requirements.txt` |
| WhiteNoise | Static files | Serve Django admin static on Render | middleware + `STORAGES` |
| Gunicorn | WSGI server | Production process | `render.yaml` start command |
| python-dotenv | `.env` loader | Local secrets | `load_dotenv` |
| httpx | HTTP client | Calls the vision LLM | `openai_compatible.py` |
| Pydantic v2 | JSON models | Validate LLM output | `nutrition/ai/schema.py` |
| Pillow | Images | Resize/re-encode uploads | `nutrition/image_utils.py` |

## Frontend

| Technology | What it is | Why | Where |
|---|---|---|---|
| React 18 | UI library | Interactive SPA | `frontend/package.json` |
| Vite 5 | Bundler / dev server | Fast local DX, `npm run build` | `vite.config.js` |
| Tailwind CSS 3 | Utility CSS | Dark “ink” + orange “brand” theme | `tailwind.config.js`, `index.css` |
| Axios | HTTP | Interceptors for JWT refresh | `src/api/client.js` |
| React Router 6 | Routing | Role-gated pages | `App.jsx` |
| Recharts | Charts | Dashboard, attendance, food kcal | pages listed in Ch. 7 |
| lucide-react | Icons | Navigation and buttons | `Layout.jsx` |

There is **no** Redux, React Query, or TypeScript in `package.json`.

## Infrastructure

| Piece | Role | Evidence |
|---|---|---|
| Render | Host Django | `render.yaml`, `backend/build.sh` |
| Vercel | Host SPA | `frontend/vercel.json` |
| Environment variables | Secrets and hosts | `.env.example` files |
| External MySQL | Data | Blueprint comments: Render has no MySQL |

Optional vision hosts (operator-configured, not hard-coded vendors in Python): any OpenAI-compatible `/v1/chat/completions` with image content. Defaults in `.env.example` point at Hugging Face’s router URL and model id `Qwen/Qwen2.5-VL-7B-Instruct`.

---

# Chapter 3 – System Architecture

See **[FITTRACK_ARCHITECTURE.md](./FITTRACK_ARCHITECTURE.md)** for full Mermaid diagrams:

1. High-level system  
2. Frontend-to-backend request flow  
3. JWT login / refresh / logout  
4. ER diagram  
5. Membership, check-in, and food-scan workflows  
6. Render + Vercel deploy

**Summary in simple language:** the browser runs React. React calls `/api/...` with a Bearer token. Django checks the token, checks the role, then uses the ORM. Money is `Decimal`. Food photos are resized, sent to an LLM (or mock), never saved as files, then confirmed into meal rows.

---

# Chapter 4 – Backend Documentation

Project package: `backend/config/`. WSGI: `config.wsgi:application`. Root URLs: `backend/config/urls.py`.

Directory (apps only):

```
backend/
  config/          settings, urls, wsgi, asgi
  core/            permissions, pagination, exceptions, validators, management commands
  accounts/        User, JWT, user admin API
  members/
  trainers/
  plans/           MembershipPlan, Membership, sell/renew services
  payments/        Payment records
  attendance/
  dashboard/       single GET aggregator
  portal/          member-only reads
  nutrition/       scans, meals, AI providers
```

## 4.1 `core`

**Responsibility:** shared API mechanics and demo data.

- `permissions.py` — `RolePermission`, `MemberPortalPermission`, role tuples.
- `pagination.py` — `StandardPagination`.
- `exceptions.py` — `ProtectedError` → HTTP 409.
- `validators.py` — phone regex `^\+?[0-9]{10,13}$`.
- `views.py` — `health` (mounted at `/api/health/`).
- Commands: `seed_data`, `update_membership_status`.

## 4.2 `accounts`

**Model:** `User` (`AbstractUser`) + `role` (`ADMIN`/`STAFF`/`TRAINER`/`MEMBER`) + `phone`.

**Views:** `LoginView` (token pair + user), `LogoutView` (blacklist), `MeView`, `UserViewSet` (admin).

**Serializers:** `UserSerializer` (includes `member_id`), `UserAdminSerializer` (password validation; blocks creating trainer/member logins here), `FitTrackTokenSerializer`.

**URLs:** `/api/auth/login|refresh|logout|me/` and `/api/auth/users/`.

## 4.3 `members`

**Model:** `Member` — profile fields, optional `user` OneToOne, optional `trainer`, `nutrition_consent_at`, auto `member_code` `FT{pk:05d}`.

**View:** `MemberViewSet` — trainers filtered to `trainer__user=request.user`. Calls `Membership.objects.sync_expired()` on queryset. Destroy deletes linked user.

**Serializer:** computed membership snapshot; optional login create (role MEMBER).

**Filter:** `MemberFilter.membership_status`.

## 4.4 `trainers`

**Model:** `Trainer` optional `user` OneToOne.

**View:** CRUD admin-only writes; `assign` / `unassign` admin+staff; `members` action.

**Serializer:** optional login role TRAINER; syncs user name/email/active on update.

## 4.5 `plans`

**Models:** `MembershipPlan` (duration map 30/90/365), `Membership` (ACTIVE/EXPIRED/CANCELLED, `effective_status`, `days_left`).

**Service:** `create_membership` — date math + optional `Payment`.

**Views:** Plan CRUD (admin writes). Membership: list/retrieve/create/destroy + `renew` + `cancel`. Trainers see only assigned members’ memberships.

## 4.6 `payments` (historical / operational records)

**This app exists and is used.** It stores **manual payment records**. It is **not** an online payment product.

**Model:** `Payment` with `receipt_no` `RCP-{pk:06d}`, methods CASH/CARD/UPI/BANK_TRANSFER, statuses PAID/PENDING/REFUNDED, `PROTECT` on member.

**View:** staff/admin only; `summary`, `receipt` (includes `GYM_*` settings).

## 4.7 `attendance`

**Model:** unique `(member, date)`.

**View:** no generic POST create; use `check-in` / `check-out`. `report` builds daily counts, top 5 members, hours 5–22.

## 4.8 `dashboard`

**View:** `DashboardView` GET. `read_roles = STAFF_ROLES` (members excluded). Builds stats, expiring memberships (7 days), plan mix, 6-month growth, 14-day attendance, recent members; finance block for admin/staff.

## 4.9 `portal`

**Views:** `MemberProfileView`, `MemberMembershipsView`, `MemberAttendanceView`. Permission: `MemberPortalPermission`.

## 4.10 `nutrition`

**Models:** `FoodScan`, `MealEntry`, `MealItem`.

**AI:** `get_food_vision_provider()` → `mock` or `openai_compatible`.

**Services:** `run_food_scan`, `validate_analysis` (kcal vs 4P+4C+9F within 25%, portion caps), `confirm_scan`, `totals_from_items`.

**Views:** scans (multipart create, JSON confirm), entries, summary, status, consent.

**Access:** `member_for_user`.

How apps communicate: membership create imports `payments.models.Payment`; dashboard imports members/payments/attendance/plans/trainers; portal imports members/plans/attendance; nutrition imports members. No Celery; food scan is **synchronous** in the request.

---

# Chapter 5 – Database Documentation

Engine: MySQL (utf8mb4, `STRICT_TRANS_TABLES`) or optional SQLite. Default PK: `BigAutoField`.

Django table names = `{app}_{model}` lowercase.

### `accounts_user`

Purpose: login. Extra columns beyond AbstractUser: `role` varchar(10), `phone` varchar(15). PK `id`. Unique `username`.

### `trainers_trainer`

PK `id`. Optional unique `user_id` → `accounts_user`. Unique `email`. Fields: `full_name`, `phone`, `specialization`, `experience_years`, `bio`, `joined_date`, `is_active`, `created_at`.

### `members_member`

PK `id`. Unique `member_code`, unique `email`. Optional `user_id` SET_NULL, optional `trainer_id` SET_NULL. `nutrition_consent_at` nullable. Demographics, emergency contacts, `height_cm` 50–260, `weight_kg` 20–400, `is_active`, timestamps.

### `plans_membershipplan`

Unique `name`. `plan_type` MONTHLY/QUARTERLY/YEARLY. `price` Decimal ≥ 1. `features` text. `is_active`.

### `plans_membership`

FK `member` CASCADE, FK `plan` **PROTECT**, optional `created_by` SET_NULL. `start_date`, `end_date`, `price` snapshot, `status`. Index `(status, end_date)`.

**Business rules:** end date inclusive (`duration_days - 1`). `effective_status` treats past `end_date` as EXPIRED unless CANCELLED.

### `payments_payment`

Unique `receipt_no`. FK `member` **PROTECT**. Optional `membership` SET_NULL. `amount` ≥ 0.01. Index `(status, paid_on)`.

### `attendance_attendance`

FK `member` CASCADE. Unique constraint `unique_attendance_per_member_per_day`. `check_in` required, `check_out` optional.

### `nutrition_foodscan`

FK `member` CASCADE, `created_by` SET_NULL. JSON `analysis`, `raw_response`. Status PENDING/SUCCEEDED/NEEDS_REVIEW/FAILED. **No image column.**

### `nutrition_mealentry`

FK `member` CASCADE. Optional OneToOne `scan`. Totals Decimal. Source AI / AI_EDITED / MANUAL. Meal types BREAKFAST/LUNCH/DINNER/SNACK/OTHER.

### `nutrition_mealitem`

FK `entry` CASCADE. Line macros + `was_edited`.

### JWT blacklist

Tables from `rest_framework_simplejwt.token_blacklist` (outstanding/blacklisted tokens). Not domain models.

ER diagram: [FITTRACK_ARCHITECTURE.md](./FITTRACK_ARCHITECTURE.md) §6.

**How records connect:** Member is the hub. Trainer assignment is a FK on Member. Memberships and payments and attendance and meals all FK to Member. A confirmed scan becomes one MealEntry; items belong to the entry. Trainers never own payments.

---

# Chapter 6 – Authentication and Role-Based Access

## JWT

1. User posts username/password.  
2. SimpleJWT issues access (default 30 min) and refresh (default 7 days).  
3. SPA stores both in `localStorage` (`fittrack_access`, `fittrack_refresh`).  
4. Axios sends access. On 401, it posts refresh, stores new pair (rotation), retries once.  
5. Logout blacklists refresh. Frontend also clears storage on unrecoverable 401 (`auth:logout` event).

## Roles

| | Admin | Staff | Trainer | Member |
|---|---|---|---|---|
| Dashboard | Yes | Yes | Own members, no finance | No (403) |
| Members | Full | Full | Read assigned | No staff UI |
| Trainers | Full | Read + assign | API list yes; **UI `/trainers` hidden** | No |
| Plans | Full | Read | Read | Portal shows own plan via membership |
| Memberships | Full | Sell/renew/cancel | Read assigned | Portal list |
| Payments | Full | Record/edit/view; delete admin | No | No |
| Attendance | Full | Check-in/out, delete | Check-in assigned | Own visits in portal |
| User accounts | Full | No | No | No |
| Portal `/me` | No | No | No | Yes |
| Food log UI | No | No | No | Yes |
| Nutrition API | Yes | Yes (needs `member`) | Assigned `member` | Self |
| Nutrition status | Yes | Yes | No | No |
| Consent POST | No | No | No | Yes |

Enforcement: `RolePermission.has_permission` compares `user.role` to `read_roles` / `write_roles` / `action_roles`. Object-level trainer filters are extra in `get_queryset`. Member portal uses `MemberPortalPermission` (must have active `member_profile`).

UI `ProtectedRoute` hides pages; **the API is the real control**.

---

# Chapter 7 – Frontend Documentation

## Structure

```
frontend/src/
  main.jsx              Router + Auth + Toast
  App.jsx               Routes
  api/client.js         Axios + token store
  api/index.js          Feature API helpers
  context/AuthContext.jsx
  context/ToastContext.jsx
  components/Layout.jsx
  components/ProtectedRoute.jsx
  components/ui/        Button, Field, Modal, Badge, StatCard, Pagination, States, Avatar, SearchInput, ConfirmDialog, PageHeader, MemberSelect
  components/members|trainers|memberships|payments|attendance|users|nutrition/
  pages/                staff screens
  pages/me/             member screens
  hooks/useFetch.js, usePagedList.js
  utils/                constants, format, validators, errors, image
```

## Routing (`App.jsx`)

| Path | Page | Roles |
|---|---|---|
| `/login` | Login | Public |
| `/` | Dashboard or redirect `/me` | Staff roles vs MEMBER |
| `/members` | Members | ADMIN, STAFF, TRAINER |
| `/trainers` | Trainers | ADMIN, STAFF |
| `/plans` | Plans | STAFF_ROLES |
| `/memberships` | Memberships | STAFF_ROLES |
| `/payments` | Payments | ADMIN, STAFF |
| `/attendance` | Attendance | STAFF_ROLES |
| `/users` | Users | ADMIN |
| `/me` | MyHome | MEMBER |
| `/me/food` | FoodLog | MEMBER |
| `/me/membership` | MyMembership | MEMBER |
| `/me/visits` | MyVisits | MEMBER |

## Auth handling

`AuthProvider` hydrates from `/auth/me/`. `login` writes tokens. Layout logout calls `/auth/logout/`.

## Axios

Base `VITE_API_URL`. Timeout 20s (nutrition upload 120s). Refresh single-flight.

## Design system

Tailwind colours `ink.*` and `brand.*`, fonts Inter + Barlow Condensed (`tailwind.config.js`). Buttons: `btn btn-primary` etc. in `index.css`.

## Charts

- Dashboard: Area/Bar/Pie revenue, growth, attendance, plan mix (`Dashboard.jsx`).
- Attendance report: `AttendanceReport.jsx`.
- Food log: 7-day kcal bars (`FoodLog.jsx`). Member home shows today’s kcal stat, not a chart.

## Navigation flows

**Admin:** Login → Dashboard → any staff nav including Users.  
**Staff:** same except Users.  
**Trainer:** Dashboard, Members, Plans, Memberships, Attendance (no Payments, Trainers, Users).  
**Member:** Home → Food log / Membership / Visits.

---

# Chapter 8 – Feature-by-Feature Explanation

## 8.1 Member management

**What:** Create and update gym members, search, filter by membership state, optional portal login.  
**Why:** Front desk source of truth.  
**UI:** `Members.jsx`, `MemberFormModal`, `MemberDetailModal`.  
**Backend:** `MemberViewSet`.  
**DB:** `members_member` (+ optional `accounts_user`).  
**Validations:** unique email, phone regex, DOB not future, inactive trainer cannot be newly assigned.  
**API:** `/api/members/`.

## 8.2 Trainer management

**What:** Trainer directory, optional login, assign members.  
**UI:** `Trainers.jsx` (admin/staff).  
**API:** `/api/trainers/`, `/assign/`, `/unassign/`, `/members/`.  
**DB:** `trainers_trainer`, `members_member.trainer_id`.

## 8.3 Membership plans

**What:** Named priced products with duration.  
**UI:** `Plans.jsx`, `PlanFormModal`. Admin-only writes.  
**API:** `/api/plans/`.

## 8.4 Membership sales and renewals

**What:** Sell a plan; renew creates a **new** membership starting after the current one; cancel sets CANCELLED.  
**UI:** `Memberships.jsx`, `SellMembershipModal`, `RenewModal`.  
**Backend:** `create_membership`.  
**API:** `POST /memberships/`, `/renew/`, `/cancel/`.

## 8.5 Payment records

**What:** Desk logs an amount, method, status; printable receipt modal.  
**What it is not:** card capture or UPI collection inside the app.  
**UI:** `Payments.jsx`, `PaymentFormModal`, `ReceiptModal`.  
**API:** `/payments/`, `/summary/`, `/receipt/`.  
**DB:** `payments_payment`. Member with payments cannot be deleted (409).

## 8.6 Attendance management

**What:** Daily log, filters, delete (staff), reports.  
**UI:** `Attendance.jsx`, `AttendanceReport.jsx`.  
**API:** `/attendance/`, `/report/`.

## 8.7 Check-in and check-out

**What:** One visit per member per day; checkout only today.  
**Validations:** active member, active membership, trainer scope.  
**API:** `POST /attendance/check-in/`, `POST /attendance/{id}/check-out/`.

## 8.8 Dashboard and analytics

**What:** Counts, expiring in 7 days, charts, recent payments (staff).  
**UI:** `Dashboard.jsx` respects `can_view_finance`.  
**API:** `GET /dashboard/`.

## 8.9 AI nutrition tracking

Implemented for **members in the UI** and for staff/trainers **via API only**. Details: Chapter 9.

---

# Chapter 9 – AI Nutrition Tracker

## Why it exists

Members want a rough calorie log without typing every ingredient. FitTrack uses a **multimodal LLM**, not a custom vision CNN.

## Photograph upload

Member Food log (`FoodLog.jsx`) downscales on the client (`utils/image.js`), then `POST /nutrition/scans/` multipart. Server `normalize_meal_image` accepts JPEG/PNG/WebP, max 5 MB, max edge `FOOD_AI_MAX_IMAGE_PX` (default 1280), strips EXIF, re-encodes JPEG.

**Images are not stored.** Only `analysis` JSON is saved on `FoodScan`.

## Consent

`POST /nutrition/consent/` sets `Member.nutrition_consent_at`. Scans without consent return 400.

## Providers

`FOOD_AI_PROVIDER`:

| Value | Class | Behaviour |
|---|---|---|
| `mock` | `MockFoodVisionProvider` | Fixed Indian plate; no network |
| `openai_compatible` | `OpenAICompatibleProvider` | `POST {FOOD_AI_BASE_URL}/chat/completions` with data-URL image |

Unknown provider raises `ValueError` at call time.

Default settings (`settings.py`): enabled true, provider `mock`, Hugging Face router URL, model `Qwen/Qwen2.5-VL-7B-Instruct`, structured output `json_schema`. Operators may switch host/model (for example Groq + `json_object`) via env without code changes.

## Prompt engineering

Files: `nutrition/ai/prompts.py`, schema version `PROMPT_VERSION` in `schema.py` (currently `"2"`).

System prompt: Indian gym nutrition assistant; split every visible item; fill kcal, protein, carbs, fat, fiber; household units; oil assumptions; ignore packaging text; `is_food` false if not food.

User prompt: meal type, optional member note, JSON field list.

## What the LLM supplies vs the backend

| From LLM (or mock) | From backend |
|---|---|
| Item names, local names, units, grams, macros, confidence, assumptions, warnings, is_food | Image validation, daily scan limit, Pydantic + unit/quantity coercion (`normalize_analysis_payload`), kcal vs macro mismatch warnings, meal **totals** as **sum of confirmed lines**, scan status |

There is **no** nutrition database integration (no USDA/IFCT lookup).

Calories on save are **not recalculated** from macros unless the user edits the form; backend sums whatever numbers are posted on confirm. Sanity check on scan: if stated kcal differs from 4×P+4×C+9×F by more than 25%, status becomes `NEEDS_REVIEW`.

## Confirmation and diary

UI `ScanResultEditor` lets the member edit lines. Confirm posts items; `source` is `AI` or `AI_EDITED`. Diary: `GET /nutrition/entries/`. Home + food log use `GET /nutrition/summary/` for 7-day kcal.

## Trainer access

API: trainers may scan/list for assigned members if they send `member`. **Frontend has no trainer nutrition screen.**

## Uncertain predictions

- Model `confidence` high/medium/low; any low item → `NEEDS_REVIEW`.  
- Warnings array shown in the review modal.  
- Member can cancel without saving.  
- Daily cap reduces abuse.  
- Failed scans store `error` text.

---

# Chapter 10 – API Documentation

Complete method/path/body tables: **[FITTRACK_API_REFERENCE.md](./FITTRACK_API_REFERENCE.md)**.

Quick map of **existing** endpoints:

| Method | Endpoint | Auth |
|---|---|---|
| GET | `/health/` | Public |
| POST | `/auth/login/` | Public |
| POST | `/auth/refresh/` | Public (refresh body) |
| POST | `/auth/logout/` | JWT |
| GET | `/auth/me/` | JWT |
| CRUD | `/auth/users/` | ADMIN |
| CRUD | `/members/` | RolePermission |
| CRUD + assign | `/trainers/` | RolePermission |
| CRUD | `/plans/` | RolePermission |
| CRD + renew/cancel | `/memberships/` | RolePermission |
| CRUD + summary/receipt | `/payments/` | ADMIN/STAFF |
| List/get/delete + check-in/out/report | `/attendance/` | RolePermission |
| GET | `/dashboard/` | Staff roles |
| GET | `/portal/profile/` `/memberships/` `/attendance/` | MEMBER |
| POST | `/nutrition/consent/` | MEMBER |
| GET | `/nutrition/status/` | ADMIN/STAFF |
| GET | `/nutrition/summary/` | STAFF_AND_MEMBER |
| POST/GET | `/nutrition/scans/` + `confirm` | STAFF_AND_MEMBER |
| GET/DELETE/manual POST | `/nutrition/entries/` | STAFF_AND_MEMBER |

---

# Chapter 11 – Installation and Local Setup

Follow **[FITTRACK_DEVELOPER_SETUP.md](./FITTRACK_DEVELOPER_SETUP.md)** (commands verified against `requirements.txt`, `package.json`, `.env.example`).

Short path:

1. Python 3.10+, Node 18+, MySQL 8.  
2. `CREATE DATABASE fittrack ... utf8mb4`.  
3. `backend`: venv, `pip install -r requirements.txt`, copy `.env.example`, `migrate`, `seed_data`, `runserver`.  
4. `frontend`: copy `.env.example`, `npm install`, `npm run dev`.  
5. Demo users: `admin` / `Admin@123`, `staff` / `Staff@123`, `arjun` / `Trainer@123`, `member` / `Member@123`.

Placeholder env only — never commit real `FOOD_AI_API_KEY` or `SECRET_KEY`.

---

# Chapter 12 – Deployment Documentation

## Backend (Render)

`render.yaml`: web service `fittrack-api`, `rootDir: backend`, Python **3.12.7**, `DEBUG=False`, generated `SECRET_KEY`, `buildCommand: bash build.sh`, `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`, health `/api/health/`.

`build.sh`: pip install, `collectstatic`, `migrate`, optional `seed_data` if `SEED_DEMO_DATA=true`.

MySQL: operator fills `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`. Default `DB_SSL_CA=/etc/ssl/certs/ca-certificates.crt`.

## Frontend (Vercel)

`frontend/vercel.json`: Vite, `npm run build`, output `dist`, SPA rewrite `/(.*) → /index.html`.

Env: `VITE_API_URL=https://<render-host>/api` (no trailing slash).

## CORS / CSRF

After Vercel URL exists, set Render `CORS_ALLOWED_ORIGINS` to that origin and `CSRF_TRUSTED_ORIGINS` as needed (typically the API HTTPS origin). `ALLOWED_HOSTS` also receives `RENDER_EXTERNAL_HOSTNAME` automatically.

## Production Django flags

When `DEBUG` is false: `SECURE_PROXY_SSL_HEADER`, secure cookies, optional `SECURE_SSL_REDIRECT`. `SECRET_KEY` is required.

## Static files

WhiteNoise `CompressedStaticFilesStorage`. No media pipeline for meal photos.

## Troubleshooting (from README + config)

Sleeping free Render dynos, missing CORS, wrong `VITE_API_URL`, missing SSL CA, demo passwords left enabled (`SEED_DEMO_DATA`).

Diagram: Architecture doc §8.

**Live production URLs are not in the repository**; this chapter documents the **files and process**, not a specific deployed instance.

---

# Chapter 13 – Security and Data Protection

## Implemented

- Django password hashers + validators on user/member/trainer password fields.  
- JWT with rotation and blacklist.  
- RBAC on every ViewSet inspected.  
- CORS allowlist (not `CORS_ALLOW_ALL`).  
- `DEBUG` default false in settings if env missing; production requires `SECRET_KEY`.  
- `.env` gitignored.  
- Phone/email uniqueness and phone regex.  
- Image type/size/pixel caps; EXIF stripped.  
- Nutrition consent timestamp.  
- Daily scan quota per user.  
- Prompt tells the model to ignore text-in-image instructions (prompt-injection hygiene; not a guarantee).  
- `ProtectedError` instead of cascading payment loss.

## Gaps (honest)

- JWT in **localStorage** (XSS).  
- No Django `DEFAULT_THROTTLE_RATES` in settings.  
- `raw_response` from the LLM is stored in MySQL (may contain prompt/image metadata depending on vendor).  
- No field-level encryption for PII.  
- Demo passwords published.  
- CSRF mainly relevant for cookie/admin; SPA uses Bearer.  
- CORS misconfiguration in production would block or over-allow origins — operator-dependent.  
- Member height/weight stored in cleartext.  
- No audit log table.  
- Groq/other keys in local `.env` must never be committed; rotate if leaked in chat or screenshots.

---

# Chapter 14 – Testing and Quality Assurance

## Automated tests

**None found.** No `tests.py`, `test_*.py`, `pytest.ini`, Jest, Vitest, or Cypress config. Do not claim tests passed.

## Test commands

Django would support `python manage.py test` once tests exist. Frontend has only `dev`, `build`, `preview`.

## Manual testing (suggested)

1. Health endpoint.  
2. Login all four demo roles; confirm redirects.  
3. Member CRUD, sell membership, payment receipt print.  
4. Check-in without membership → 400; with membership → 201; second check-in → 400.  
5. Trainer cannot open payments; cannot check in unassigned member.  
6. Member cannot open `/dashboard` API.  
7. Food mock scan → confirm → summary kcal increases.  
8. Optional live LLM scan with a real photo; expect possible `NEEDS_REVIEW` and rate limits.

## AI evaluation

No offline accuracy benchmark is in the repo. Informal photo tests (for example a thali) showed item splitting with imperfect dish names — that is expected LLM behaviour, not a signed-off metric.

## Known bugs / sharp edges (from code + prior scans)

- LLM dish labelling can be wrong; confirmation is mandatory for good data.  
- Summary omits fiber.  
- Upstream HTTP 429 not specially mapped.  
- Confirm used to fail if JSON hit multipart-only parsers; current `FoodScanViewSet.get_parsers()` uses JSON except on `create`.

---

# Chapter 15 – Known Limitations

| Area | Current status | Limitation | Suggested improvement |
|---|---|---|---|
| Automated tests | Absent | No safety net | pytest + API tests; frontend component tests |
| CI | Absent | Broken main possible | GitHub Actions migrate + build |
| Auth storage | localStorage | Token theft via XSS | httpOnly cookies |
| Payments | Manual records | Not online pay | Keep explicit “record only” UX |
| Nutrition UI | Member only | Staff cannot review meals in UI | Member-detail nutrition tab |
| Photos | Not stored | No audit of inputs | Optional short-lived storage |
| Nutrition data | LLM only | No food composition DB | Optional reference lookup |
| Summary | kcal P C F | No fiber in chart API | Add `fiber_g` |
| Member portal | Read-mostly | Cannot update profile | PATCH portal profile |
| Trainer UI | Partial vs API | No `/trainers` for trainers | Profile page |
| Deploy | Config present | Hosted URL not verified here | Operator deploy checklist |
| Rate limits | LLM vendor | 429 on free tiers | Retry/backoff + UI copy |
| Multi-gym | Single DB | One gym assumption | Tenancy if needed later |

---

# Chapter 16 – Future Enhancements

Not implemented unless listed in Chapter 8:

- Staff/trainer nutrition monitoring screens  
- Nutrition history exports  
- Workout and diet plans  
- Body measurement history  
- QR attendance  
- Automated expiry / payment reminders  
- Stronger analytics  
- Automated testing and CI/CD  
- Hardening (throttles, security headers, cookie auth)

Member portal and AI calorie tracking are **in progress / present**, not future-only.

---

# Chapter 17 – Developer Handover

## Important directories

| Path | Why |
|---|---|
| `backend/config/settings.py` | Env, JWT, FOOD_AI, DB |
| `backend/core/permissions.py` | Roles |
| `backend/plans/services.py` | Sell/renew dates + payment insert |
| `backend/nutrition/services.py` | Scan pipeline |
| `backend/nutrition/ai/` | Prompts, schema, providers |
| `frontend/src/api/` | All HTTP |
| `frontend/src/App.jsx` | Routes |
| `render.yaml` / `frontend/vercel.json` | Hosting |

## Migrations

Change models → `makemigrations` → commit files → `migrate`. Do not rely on Render’s fallback `makemigrations` in `build.sh` except as a safety net.

## API workflow

Add serializer + viewset + router include in `config/urls.py`. Set `read_roles`/`write_roles`. Add `frontend/src/api/index.js` helper and a page.

## Frontend workflow

Page in `pages/`, route + nav roles, reuse `ui/` components, `usePagedList` for tables.

## Troubleshooting

See setup doc §9.

## Pending technical tasks

Tests, staff nutrition UI, fiber on summary, 429 handling, optional photo retention policy, disable demo seed in production, rotate any leaked API keys.

## Practices

- Keep money as Decimal.  
- Do not add a payment gateway unless explicitly designed (PCI).  
- Treat LLM output as untrusted; keep confirm step.  
- Never commit `.env`.

---

# Chapter 18 – Project Summary

FitTrack is a **Django REST + React** gym operations system with **JWT RBAC**, membership lifecycle, **manual payment receipts**, attendance, dashboards, a **member portal**, and an **optional vision-LLM food log**.

**Achievements:** coherent domain model, server-enforced roles, seed data, deploy blueprints, nutrition pipeline with mock and OpenAI-compatible providers, human confirmation of macros (kcal, protein, carbs, fat, fiber).

**Engineering decisions:** PyMySQL for Windows-friendly MySQL; SimpleJWT for SPA auth; synchronous LLM calls; no food composition database; payments as bookkeeping.

**Status:** core gym desk features and member food log are present. Staff nutrition UI, automated tests, and production hardening are incomplete. Payment **processing** is out of scope.

**Conclusion:** a new developer can run the stack from the setup guide, extend APIs via existing ViewSets, and should treat nutrition numbers as estimates until a member confirms them.

---

*Documentation generated from repository inspection. It does not certify a live deployment or unpublished branches.*
