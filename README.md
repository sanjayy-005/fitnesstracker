# FitTrack – Gym Management System

FitTrack is a full-stack web app for **one gym**: members, trainers, membership plans, renewals, **desk payment records** (printable receipts), attendance, role-based dashboards, a **member portal**, and an optional **AI meal photo log**.

It is **not** an online payment gateway. Money screens store cash / UPI / card / bank-transfer **records** entered by staff.

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Recharts, React Router, Axios |
| Backend | Python, Django 5.2, Django REST Framework |
| Database | MySQL 8 locally; Supabase PostgreSQL for hosted deployment |
| Auth | JWT (SimpleJWT, refresh rotation + blacklist) |
| Deploy config | Render (API) + Cloudflare Pages (SPA) + Supabase PostgreSQL |

https://fitnesstracker-edt.pages.dev

## Documentation

| Document | Contents |
|---|---|
| [docs/FITTRACK_TECHNICAL_DOCUMENTATION.md](docs/FITTRACK_TECHNICAL_DOCUMENTATION.md) | Full technical documentation (architecture through handover) |
| [docs/FITTRACK_ARCHITECTURE.md](docs/FITTRACK_ARCHITECTURE.md) | Diagrams, ER model, workflows |
| [docs/FITTRACK_DEVELOPER_SETUP.md](docs/FITTRACK_DEVELOPER_SETUP.md) | Local install (macOS, Linux, Windows) |
| [docs/FITTRACK_API_REFERENCE.md](docs/FITTRACK_API_REFERENCE.md) | HTTP endpoints |
| [docs/FITTRACK_PROJECT_STATUS.md](docs/FITTRACK_PROJECT_STATUS.md) | Implemented vs partial vs planned |

## What is implemented

- **Dashboard** (admin / staff / trainer): counts, charts, expiring memberships. Revenue only for admin and staff.
- **Members, trainers, plans, memberships:** CRUD as allowed by role; sell, renew, cancel; auto expiry helpers.
- **Payments:** record, filter, summary, printable receipt JSON/UI.
- **Attendance:** check-in / check-out (one visit per member per day), reports.
- **Users:** admin-only login accounts. Trainer and member logins are created from Trainers / Members.
- **Member portal:** home, membership history, visits, food log (consent + photo scan + confirm macros).

Roles are enforced in `backend/core/permissions.py`. The UI hides routes the API would refuse.

| Capability | Admin | Front desk (STAFF) | Trainer | Member |
|---|---|---|---|---|
| Staff dashboard | Yes | Yes | Assigned members, no revenue | No |
| Members | Full | Full | Read assigned | Portal only |
| Trainers screen | Full | View, assign | API only; no `/trainers` page | No |
| Plans | Full | View | View | Via own membership |
| Memberships | Full | Sell, renew, cancel | View assigned | Own history |
| Payment records | Full | Record / edit | No | No |
| Attendance | Full | Check-in/out, delete | Check-in assigned | Own visits |
| User accounts | Full | No | No | No |
| Food log UI | No | No | No | Yes |
| Nutrition API | Yes | Yes (`member` id) | Assigned members | Self |

## Repository layout

```
fittrack-gym-management/
├── backend/                 Django API
│   ├── config/              settings, urls, wsgi
│   ├── core/                permissions, pagination, seed_data
│   ├── accounts/ members/ trainers/ plans/ payments/ attendance/
│   ├── dashboard/ portal/ nutrition/
│   ├── build.sh             Render
│   ├── requirements.txt
│   └── .env.example
├── frontend/                React SPA
│   ├── src/api/             Axios + JWT refresh
│   ├── src/pages/           Staff + pages/me (member)
│   ├── vercel.json
│   └── .env.example
├── docs/                    Technical documentation
├── render.yaml
└── README.md
```

## Quick start

You need **Python 3.10+**, **Node.js 18+**, **MySQL 8**, and **Git**. Step-by-step: [docs/FITTRACK_DEVELOPER_SETUP.md](docs/FITTRACK_DEVELOPER_SETUP.md).

```bash
# MySQL
CREATE DATABASE fittrack CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # set DB_PASSWORD
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

```bash
cd frontend
cp .env.example .env              # VITE_API_URL=http://127.0.0.1:8000/api
npm install
npm run dev
```

- API: http://127.0.0.1:8000/api/health/
- App: http://localhost:5173

### Demo logins (`seed_data`)

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@123` |
| Front desk | `staff` | `Staff@123` |
| Trainer | `arjun` (also `priya`, `rahul`) | `Trainer@123` |
| Member | `member` | `Member@123` |

`python manage.py seed_data --reset` wipes gym data and reloads the demo. Change these passwords on any shared server.

## Food calorie scan

Default `FOOD_AI_PROVIDER=mock` (no API key). For a real vision model set `FOOD_AI_PROVIDER=openai_compatible`, `FOOD_AI_BASE_URL`, `FOOD_AI_MODEL`, and `FOOD_AI_API_KEY`. Details: technical documentation Chapter 9.

Meal photos are analysed and **not stored** as files.

## Deploy

Recommended setup: `render.yaml` (Django API on Render) + Cloudflare Pages (React SPA) + Supabase PostgreSQL. The backend supports PostgreSQL for hosting; local development can continue to use MySQL. For Cloudflare Pages, connect this repository, set the project root to `frontend`, build command to `npm run build`, output directory to `dist`, and build variable `VITE_API_URL=https://api.<your-domain>/api`. The Pages SPA fallback is in `frontend/public/_redirects`.

Use Cloudflare DNS for your domain, with the frontend on the apex/www hostname and `api.<your-domain>` mapped to the Render service. Set the Render `ALLOWED_HOSTS` to include the API hostname and `CORS_ALLOWED_ORIGINS` to the exact frontend origin (for example `https://<your-domain>`). In Render, use the Supabase Session pooler connection information and keep `DB_SSLMODE=require`. See technical documentation Chapter 12 for deployment steps.

Never commit `backend/.env` or `frontend/.env`.
