# FitTrack – Developer Setup

Local installation for the code in this repository. Commands below match `backend/requirements.txt`, `frontend/package.json`, `backend/.env.example`, and `frontend/.env.example`.

For architecture, see [FITTRACK_ARCHITECTURE.md](./FITTRACK_ARCHITECTURE.md). For APIs, see [FITTRACK_API_REFERENCE.md](./FITTRACK_API_REFERENCE.md).

---

## 1. Prerequisites

| Tool | Used for | Notes |
|---|---|---|
| Python **3.10+** | Django | Render blueprint pins **3.12.7** (`render.yaml`) |
| Node.js **18+** | Vite / React | 20 LTS is a reasonable choice |
| npm | Frontend packages | Comes with Node |
| MySQL **8** | Primary database | Optional: `DB_ENGINE=sqlite` for experiments only |
| Git | Clone | |

This project was developed with Django **5.2.x** and React **18.3**.

---

## 2. Clone the repository

```bash
git clone <your-remote-url> fittrack-gym-management
cd fittrack-gym-management
```

---

## 3. MySQL database

Create an empty database (utf8mb4):

```sql
CREATE DATABASE fittrack CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Default local settings in `.env.example` are:

- Host `127.0.0.1`
- Port `3306`
- User `root`
- Database name `fittrack`

Set `DB_PASSWORD` to your actual MySQL password. Leave `DB_SSL_CA` empty for a typical local install.

**macOS (Homebrew) example:** install MySQL, start the service, then create the database with the `mysql` client.

**Windows:** MySQL Installer or MySQL Workbench is fine. If `py` launches Python, use `py` instead of `python` in the commands below.

---

## 4. Backend

From the repository root:

```bash
cd backend
python3 -m venv venv
```

Activate:

```bash
# macOS / Linux
source venv/bin/activate

# Windows Command Prompt
venv\Scripts\activate
```

Install packages:

```bash
pip install -r requirements.txt
```

Create environment file:

```bash
# macOS / Linux
cp .env.example .env

# Windows
copy .env.example .env
```

Edit `backend/.env`. **Placeholder example** (never commit real secrets):

```env
SECRET_KEY=replace-with-a-long-random-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
TIME_ZONE=Asia/Kolkata

DB_ENGINE=mysql
DB_NAME=fittrack
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_SSL_CA=

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CSRF_TRUSTED_ORIGINS=

ACCESS_TOKEN_MINUTES=30
REFRESH_TOKEN_DAYS=7

GYM_NAME=FitTrack Gym
GYM_ADDRESS=12 Fitness Street, Coimbatore, Tamil Nadu 641001
GYM_PHONE=+91 98765 43210
GYM_EMAIL=hello@fittrack.example

FOOD_AI_ENABLED=true
FOOD_AI_PROVIDER=mock
FOOD_AI_BASE_URL=https://router.huggingface.co/v1
FOOD_AI_MODEL=Qwen/Qwen2.5-VL-7B-Instruct
FOOD_AI_API_KEY=
FOOD_AI_STRUCTURED_OUTPUT=json_schema
FOOD_AI_TIMEOUT_SECONDS=60
FOOD_AI_MAX_IMAGE_PX=1280
FOOD_AI_DAILY_SCANS_PER_USER=20
```

Apply schema and demo data:

```bash
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

- API: http://127.0.0.1:8000/api/
- Health: http://127.0.0.1:8000/api/health/ → `{"status": "ok", "database": "up"}`
- Django admin: http://127.0.0.1:8000/admin/

`seed_data` **does nothing** if the database already has users. To wipe demo data and reload:

```bash
python manage.py seed_data --reset
```

`--reset` deletes gym data including nutrition rows (see `seed_data.py`). Use only on local or disposable databases.

Optional: mark overdue memberships expired (also happens automatically when some list endpoints run):

```bash
python manage.py update_membership_status
```

### SQLite (experiments only)

Set `DB_ENGINE=sqlite` in `.env`. Django then uses `backend/db.sqlite3`. This path is implemented in `settings.py` but is not the documented production database.

---

## 5. Frontend

Open a **second** terminal:

```bash
cd frontend
cp .env.example .env
# Windows: copy .env.example .env
npm install
npm run dev
```

`frontend/.env.example`:

```env
VITE_API_URL=http://127.0.0.1:8000/api
```

Open http://localhost:5173 (Vite is configured for port **5173** in `vite.config.js`).

Restart `npm run dev` after changing `VITE_API_URL` (Vite inlines env at startup).

---

## 6. Demo logins

Created by `python manage.py seed_data` (`backend/core/management/commands/seed_data.py`):

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@123` |
| Front desk | `staff` | `Staff@123` |
| Trainer | `arjun` (also `priya`, `rahul`) | `Trainer@123` |
| Member | `member` | `Member@123` |

These passwords are **public demo values**. Change them before sharing a live deployment.

The demo member login is linked to the first member, with nutrition consent already set and one sample breakfast meal.

---

## 7. Food AI locally

Default: `FOOD_AI_PROVIDER=mock`. Scans return a fixed sample plate (rajma chawal + roti) without an API key.

For a real vision model, set:

```env
FOOD_AI_ENABLED=true
FOOD_AI_PROVIDER=openai_compatible
FOOD_AI_BASE_URL=https://example-openai-compatible-host/v1
FOOD_AI_MODEL=your-vision-model-id
FOOD_AI_API_KEY=your-key
FOOD_AI_STRUCTURED_OUTPUT=json_object
FOOD_AI_TIMEOUT_SECONDS=90
```

Use `json_schema` only if the host supports OpenAI-style `response_format.json_schema`. Some hosts (for example Groq) work more reliably with `json_object`. The repository default model id is `Qwen/Qwen2.5-VL-7B-Instruct` on Hugging Face’s router URL; operators may point `FOOD_AI_BASE_URL` and `FOOD_AI_MODEL` at any compatible vision endpoint.

Restart Django after changing `.env`.

Daily cap: `FOOD_AI_DAILY_SCANS_PER_USER` (default 20) counts scans by **created_by user** for the local date.

---

## 8. Useful commands

| Command | Purpose |
|---|---|
| `python manage.py migrate` | Apply migrations |
| `python manage.py makemigrations` | Generate migrations after model changes (commit the files) |
| `python manage.py createsuperuser` | Admin user (role forced to `ADMIN` in `accounts.UserManager`) |
| `python manage.py collectstatic` | Used on Render via `build.sh` |
| `npm run build` | Production SPA (`frontend/dist`) |
| `npm run preview` | Preview production build (port 4173) |

There is **no** `pytest` / `manage.py test` suite in the repository at the time of writing.

---

## 9. Troubleshooting

| Symptom | Likely cause |
|---|---|
| `Access denied for user` | Wrong `DB_USER` / `DB_PASSWORD` |
| `Unknown database 'fittrack'` | Database not created |
| Health `database: down` | MySQL not running or SSL required |
| Frontend cannot reach API | Backend down, or `VITE_API_URL` missing `/api` |
| CORS error in browser | Origin not in `CORS_ALLOWED_ORIGINS` (no trailing slash) |
| PowerShell venv blocked | `Set-ExecutionPolicy -Scope Process Bypass` or use `cmd` |
| Scan 503 | `FOOD_AI_ENABLED=false` or `openai_compatible` without `FOOD_AI_API_KEY` |
| Scan 400 daily limit | Wait until next local day or raise the env cap on a private machine |
| Confirm scan 415 | Fixed in current code: confirm uses JSON parsers; recreate must be multipart |

---

## 10. Production deploy (summary)

Full steps: [FITTRACK_TECHNICAL_DOCUMENTATION.md](./FITTRACK_TECHNICAL_DOCUMENTATION.md) Chapter 12.

1. Create a Supabase project and choose its Session pooler connection details.
2. Render blueprint: `render.yaml`, root `backend`, `build.sh` then gunicorn. Set `ALLOWED_HOSTS` to include the custom API hostname and enter the Supabase pooler values in `DB_HOST`, `DB_PORT`, `DB_USER`, and `DB_PASSWORD`; use `DB_NAME=postgres`, `DB_ENGINE=postgresql`, and `DB_SSLMODE=require`.
3. Cloudflare Pages: connect the repository, set root directory to `frontend`, build command to `npm run build`, output directory to `dist`, and build variable `VITE_API_URL=https://api.<your-domain>/api`.
4. In Cloudflare DNS, point the API subdomain to the Render service and configure your frontend domain for Pages. Set Render `CORS_ALLOWED_ORIGINS` to the exact frontend origin, such as `https://<your-domain>` (no trailing slash).
5. Set `SEED_DEMO_DATA=false` after first seed and change demo passwords. Django migrations create the schema but do not transfer records from an existing MySQL database.

Never commit `backend/.env` or `frontend/.env` (listed in `.gitignore`).
