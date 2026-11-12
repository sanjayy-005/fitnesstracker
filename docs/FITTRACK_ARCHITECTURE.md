# FitTrack – System Architecture

This document describes the architecture that is implemented in the repository. It complements [FITTRACK_TECHNICAL_DOCUMENTATION.md](./FITTRACK_TECHNICAL_DOCUMENTATION.md).

---

## 1. High-level system architecture

FitTrack is a **split web application**: a React single-page app talks to a Django REST API. The API stores gym data in a relational database: MySQL is the local-development default, and PostgreSQL is supported for Supabase hosting. Authentication uses **JWT** (access + refresh). Food photo analysis is optional and calls an **OpenAI-compatible vision LLM** (or a local mock).

```mermaid
flowchart LR
  subgraph Client["Browser"]
    SPA["React 18 SPA<br/>Vite + Tailwind"]
  end

  subgraph API["Django 5.2 on Render or localhost"]
    DRF["Django REST Framework"]
    JWT["SimpleJWT"]
    APPS["Domain apps:<br/>accounts, members, trainers,<br/>plans, payments, attendance,<br/>dashboard, portal, nutrition"]
  end

  subgraph Data["Data"]
    DB["MySQL locally<br/>Supabase PostgreSQL when hosted"]
    BL["JWT blacklist tables"]
  end

  subgraph External["Optional external"]
    LLM["OpenAI-compatible vision API<br/>e.g. Groq or Hugging Face Router"]
  end

  SPA -->|"HTTPS JSON + JWT<br/>CORS"| DRF
  DRF --> JWT
  DRF --> APPS
  APPS --> DB
  JWT --> BL
  APPS -->|"multipart image<br/>when FOOD_AI_PROVIDER=openai_compatible"| LLM
```

**In simple language:** the gym staff and members use a website. The website never talks to the database itself. It asks the Django API. The API checks who is logged in, applies role rules, then reads or writes the database. For a meal photo, the API shrinks the image, sends it to a vision model, validates the JSON, and only then lets the member save a meal.

**Verified from:** `frontend/src/api/client.js`, `backend/config/settings.py`, `backend/config/urls.py`, `backend/nutrition/ai/registry.py`, `render.yaml`.

---

## 2. Frontend architecture

```mermaid
flowchart TB
  MAIN["main.jsx"]
  MAIN --> ROUTER["BrowserRouter"]
  ROUTER --> TOAST["ToastProvider"]
  TOAST --> AUTH["AuthProvider"]
  AUTH --> APP["App.jsx routes"]
  APP --> LOGIN["/login"]
  APP --> PROT["ProtectedRoute + Layout"]
  PROT --> STAFF["Staff screens"]
  PROT --> ME["Member portal /me/*"]
  STAFF --> API["api/index.js"]
  ME --> API
  API --> AXIOS["axios instance<br/>Bearer token + refresh"]
```

- **Routing:** `frontend/src/App.jsx` with React Router v6.
- **Auth state:** `AuthContext` loads `/auth/me/` if an access token exists in `localStorage`.
- **HTTP:** one Axios instance (`frontend/src/api/client.js`) attaches `Authorization: Bearer …` and retries once after `POST /auth/refresh/`.
- **UI:** Tailwind “ink” (near-black) + “brand” (orange). Charts use Recharts on Dashboard, Attendance reports, and member Food log.

Members and staff share the same SPA. After login, `HomeRedirect` sends `MEMBER` to `/me` and everyone else to the staff dashboard.

---

## 3. Backend architecture

Django project package: `backend/config/` (`settings.py`, `urls.py`, `wsgi.py`).

| App | Role in architecture |
|---|---|
| `core` | Permissions, pagination, exception handler, `seed_data`, `update_membership_status`, health helper |
| `accounts` | Custom `User` with `role`, JWT login/logout, admin user CRUD |
| `members` | Member master data + optional member login |
| `trainers` | Trainer master data + optional trainer login + assign members |
| `plans` | Plans and memberships (sell / renew / cancel) |
| `payments` | Manual payment **records** and printable receipt JSON (not a payment gateway) |
| `attendance` | Check-in / check-out / reports |
| `dashboard` | Aggregated stats for staff/trainers |
| `portal` | Member self-service reads (profile, memberships, visits) |
| `nutrition` | Food scans, meal diary, vision providers |

Requests enter `config/urls.py` under `/api/` (except Django admin at `/admin/`).

---

## 4. Frontend-to-backend request flow

```mermaid
sequenceDiagram
  participant U as User
  participant UI as React page
  participant AX as Axios client
  participant API as Django view
  participant DB as Relational database

  U->>UI: Click / submit
  UI->>AX: api.get/post(...)
  AX->>AX: Add Bearer access token
  AX->>API: HTTPS /api/...
  API->>API: JWTAuthentication + RolePermission
  API->>DB: Query / write
  DB-->>API: Rows
  API-->>AX: JSON (paginated lists as count/next/previous/results)
  alt HTTP 401 and refresh token exists
    AX->>API: POST /auth/refresh/
    API-->>AX: new access (+ rotated refresh)
    AX->>API: Retry original request
  end
  AX-->>UI: data
  UI-->>U: Screen update or toast
```

List endpoints use `core.pagination.StandardPagination` (`page`, `page_size` up to 100, default 10).

---

## 5. Authentication and JWT flow

Configured in `backend/config/settings.py` (`SIMPLE_JWT`):

- Access lifetime: `ACCESS_TOKEN_MINUTES` (default **30**).
- Refresh lifetime: `REFRESH_TOKEN_DAYS` (default **7**).
- `ROTATE_REFRESH_TOKENS = True`
- `BLACKLIST_AFTER_ROTATION = True`
- `UPDATE_LAST_LOGIN = True`

```mermaid
sequenceDiagram
  participant B as Browser
  participant L as LoginView
  participant R as TokenRefreshView
  participant O as LogoutView
  participant BL as token_blacklist

  B->>L: POST /api/auth/login/ {username, password}
  L-->>B: {access, refresh, user}
  Note over B: Tokens stored in localStorage<br/>keys fittrack_access / fittrack_refresh

  loop API calls
    B->>B: Authorization Bearer access
  end

  B->>R: POST /api/auth/refresh/ {refresh}
  R->>BL: Blacklist old refresh
  R-->>B: {access, refresh}

  B->>O: POST /api/auth/logout/ {refresh}
  O->>BL: Blacklist refresh
  O-->>B: Logged out
```

Login uses `FitTrackTokenSerializer`, which adds `role` and `username` into the JWT payload and returns a `user` object (including `member_id` for member accounts).

**Limitation:** tokens live in `localStorage` (XSS-accessible). There is no httpOnly cookie session for the SPA.

---

## 6. Database relationships

```mermaid
erDiagram
  USER ||--o| TRAINER : "optional login"
  USER ||--o| MEMBER : "optional login"
  TRAINER ||--o{ MEMBER : "assigned to"
  MEMBER ||--o{ MEMBERSHIP : "purchases"
  PLAN ||--o{ MEMBERSHIP : "sold as"
  MEMBER ||--o{ PAYMENT : "pays"
  MEMBERSHIP ||--o{ PAYMENT : "optional link"
  USER ||--o{ PAYMENT : "received_by"
  MEMBER ||--o{ ATTENDANCE : "visits"
  USER ||--o{ ATTENDANCE : "marked_by"
  MEMBER ||--o{ FOODSCAN : "scans"
  MEMBER ||--o{ MEALENTRY : "eats"
  FOODSCAN ||--o| MEALENTRY : "confirmed as"
  MEALENTRY ||--o{ MEALITEM : "lines"
  USER ||--o{ MEMBERSHIP : "created_by"
  USER ||--o{ FOODSCAN : "created_by"
  USER ||--o{ MEALENTRY : "created_by"

  USER {
    bigint id PK
    string username
    string role
  }
  MEMBER {
    bigint id PK
    string member_code UK
    bigint user_id FK
    bigint trainer_id FK
  }
  TRAINER {
    bigint id PK
    bigint user_id FK
  }
  PLAN {
    bigint id PK
    string name UK
    string plan_type
  }
  MEMBERSHIP {
    bigint id PK
    bigint member_id FK
    bigint plan_id FK
    date end_date
    string status
  }
  PAYMENT {
    bigint id PK
    string receipt_no UK
    decimal amount
  }
  ATTENDANCE {
    bigint id PK
    date date
  }
  FOODSCAN {
    bigint id PK
    json analysis
    string status
  }
  MEALENTRY {
    bigint id PK
    decimal total_kcal
  }
  MEALITEM {
    bigint id PK
    decimal kcal
  }
```

Django table names follow `app_model` (for example `members_member`, `plans_membership`, `nutrition_foodscan`). Custom user table is `accounts_user`. SimpleJWT blacklist tables are created by `rest_framework_simplejwt.token_blacklist`.

**How the gym domain connects:**

1. A **Member** is the person who trains. They may have a login (`User.role = MEMBER`).
2. A **Trainer** may have a login (`User.role = TRAINER`). Members optionally point at one trainer.
3. A **Membership** is one sold period of a **MembershipPlan**. Renewals create a **new** membership row.
4. A **Payment** is a desk-recorded amount (cash, UPI, card, bank transfer). It may point at a membership. Members with payments cannot be hard-deleted (`on_delete=PROTECT`).
5. **Attendance** is one visit per member per day (`unique_attendance_per_member_per_day`).
6. **FoodScan** holds model JSON, not the photo. Confirming a scan creates **MealEntry** + **MealItem** rows.

---

## 7. Main business workflows

### 7.1 Sell or renew a membership

```mermaid
flowchart TD
  A[Staff opens Sell / Renew] --> B[POST /api/memberships/ or /renew/]
  B --> C[plans.services.create_membership]
  C --> D{Active membership already?}
  D -->|yes and no start_date| E[Start = day after current end]
  D -->|no| F[Start = today]
  E --> G[End = start + duration_days - 1]
  F --> G
  G --> H[Insert Membership]
  H --> I{record_payment?}
  I -->|yes| J[Insert Payment PAID]
  I -->|no| K[Membership only]
  J --> L[201 MembershipSerializer]
  K --> L
```

### 7.2 Check-in

```mermaid
flowchart TD
  A[POST /attendance/check-in/ member id] --> B{Trainer?}
  B -->|yes| C{Assigned to this trainer?}
  C -->|no| X[403]
  C -->|yes| D
  B -->|no| D{Member active?}
  D -->|no| Y[400]
  D -->|yes| E[sync_expired]
  E --> F{Active membership?}
  F -->|no| Y2[400 renew first]
  F -->|yes| G{Already checked in today?}
  G -->|yes| Y3[400]
  G -->|no| H[Create Attendance]
```

### 7.3 Food photo scan (member)

```mermaid
sequenceDiagram
  participant M as Member UI
  participant API as FoodScanViewSet
  participant IMG as image_utils
  participant P as Provider mock or OpenAI-compatible
  participant LLM as External LLM
  participant DB as Relational database

  M->>API: POST /nutrition/consent/
  M->>API: multipart image + meal_type + note
  API->>API: consent, daily limit, member_for_user
  API->>IMG: JPEG/PNG/WebP, max 5 MB, resize, strip EXIF
  API->>DB: FoodScan PENDING
  API->>P: analyze(bytes)
  alt openai_compatible
    P->>LLM: chat/completions + image data URL
    LLM-->>P: JSON items + macros
  else mock
    P-->>API: fixed demo plate
  end
  API->>API: Pydantic + calorie/macro sanity checks
  API->>DB: SUCCEEDED / NEEDS_REVIEW / FAILED
  API-->>M: analysis JSON
  M->>API: POST /scans/{id}/confirm/ edited items
  API->>DB: MealEntry + MealItem
```

Photos are **not** stored as files after analysis (`FoodScan` has no `ImageField`). The UI disclaimer in `FoodLog.jsx` states this.

---

## 8. Deployment architecture

```mermaid
flowchart LR
  subgraph CloudflarePages["Cloudflare Pages"]
    FE["Static SPA<br/>frontend/dist"]
  end
  subgraph Render
    Gunicorn["gunicorn config.wsgi"]
    WN["WhiteNoise staticfiles"]
    DJ["Django"]
  end
  subgraph ExternalDB["Supabase"]
    MY["PostgreSQL<br/>Session pooler"]
  end
  User --> FE
  FE -->|"VITE_API_URL .../api"| Gunicorn
  Gunicorn --> DJ
  DJ --> WN
  DJ --> MY
```

**Verified from:** `render.yaml` (Python 3.12.7, `bash build.sh`, health `/api/health/`), `backend/build.sh` (collectstatic, migrate, optional `seed_data`), Cloudflare Pages build settings and `frontend/public/_redirects` (SPA fallback to `index.html`).

The Render blueprint uses Supabase PostgreSQL through its Session pooler with SSL required. Operators provide the pooler `DB_*` credentials. Local development continues to default to MySQL.

Default production food AI in `render.yaml` is `FOOD_AI_PROVIDER=mock` unless an operator sets a real key.

---

## 9. External services (as implemented)

| Service | Required? | Where configured |
|---|---|---|
| Supabase PostgreSQL | Hosted deployment | `DB_ENGINE=postgresql`, `DB_*`, `DB_SSLMODE=require` |
| MySQL | Local-development default | `DB_ENGINE=mysql`, `DB_*` |
| Vision LLM | No (mock works) | `FOOD_AI_*` |
| Render | Optional hosting | `render.yaml` |
| Cloudflare Pages | Recommended SPA hosting | Pages build settings, `frontend/public/_redirects` |
| Vercel | Optional alternative SPA hosting | `frontend/vercel.json` |

There is **no** Stripe, Razorpay, or other payment processor in the codebase. Payments are staff-entered records.

There is **no** dedicated nutrition food composition database (USDA, IFCT, etc.). Macros come from the LLM (or mock) and are summed in `nutrition/services.py`.
