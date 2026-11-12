# FitTrack – Project Status

Honest inventory of what exists in the repository versus what does not. This is not a marketing list.

Inspected: Django apps under `backend/`, React app under `frontend/src/`, `render.yaml`, `frontend/public/_redirects`, `frontend/vercel.json`, `backend/build.sh`, `README.md`, `.env.example` files. Automated tests were **not** found. Production deploy status of any live URL was **not** verified from this repository.

---

## 1. Implemented features

| Area | Status | Evidence |
|---|---|---|
| JWT login, refresh, logout blacklist | Implemented | `accounts/views.py`, SimpleJWT settings |
| Roles ADMIN, STAFF, TRAINER, MEMBER | Implemented | `accounts/models.py` `Role` |
| Staff member CRUD, search, filters | Implemented | `members/`, `frontend/src/pages/Members.jsx` |
| Optional member login from Members form | Implemented | `MemberSerializer` username/password |
| Trainer CRUD, assign/unassign | Implemented | `trainers/views.py`, Trainers page (admin/staff UI) |
| Optional trainer login | Implemented | `TrainerSerializer` |
| Plans CRUD (admin write) | Implemented | `plans/views.py` |
| Sell / renew / cancel membership | Implemented | `plans/services.py`, Memberships page |
| Payment **records** (cash/UPI/card/bank), receipts JSON + print UI | Implemented | `payments/`, `ReceiptModal.jsx` |
| Attendance check-in/out, daily unique, reports | Implemented | `attendance/views.py` |
| Staff dashboard + Recharts | Implemented | `dashboard/views.py`, `Dashboard.jsx` |
| Trainer-scoped dashboard (no finance) | Implemented | `DashboardView` `can_view_finance` |
| Member portal: home, membership list, visits | Implemented | `portal/`, `/me`, `/me/membership`, `/me/visits` |
| Member food log: consent, photo scan, review, save | Implemented | `nutrition/`, `FoodLog.jsx` |
| Meal diary list + 7-day kcal chart (member) | Implemented | `NutritionSummaryView`, Food log / My Home |
| Manual meal API | Implemented (API) | `POST /nutrition/entries/manual/` |
| Mock vision provider | Implemented | `nutrition/ai/mock_provider.py` |
| OpenAI-compatible vision provider | Implemented | `nutrition/ai/openai_compatible.py` |
| Demo seed data including member login | Implemented | `seed_data.py` |
| Render API + Cloudflare Pages SPA config | Implemented | `render.yaml`, Pages build settings, `frontend/public/_redirects` |
| Django admin for core gym models | Implemented | `accounts`, `members`, `trainers`, `plans`, `payments`, `attendance` `admin.py` |

---

## 2. Partially implemented

| Area | What works | What is missing |
|---|---|---|
| AI nutrition for staff/trainers | API allows staff/admin/trainer scans if `member` id is sent; trainers scoped to assigned members (`nutrition/access.py`) | **No** staff or trainer nutrition pages in `App.jsx` |
| Nutrition summary | Daily kcal + P/C/F for a member | Fiber is stored on meals but **not** included in summary aggregates; no staff nutrition dashboard |
| Manual meals | Backend `create_manual` | Member Food log UI only exposes photo scan + list, not a full manual-entry form |
| Trainer product surface | API lets trainers read members/memberships/attendance/dashboard | Trainers page is **ADMIN_STAFF** in the UI; trainers cannot open `/trainers` |
| Nutrition Django admin | Models exist | No `nutrition/admin.py` |
| Food photos | Analysed in memory | Images are **not** persisted (no `ImageField` / object storage) |
| Food AI in production blueprint | Env keys exist | Default `FOOD_AI_PROVIDER=mock` on Render |
| Member profile | GET `/portal/profile/` | No member self-edit of phone, address, or password |
| CI / quality | Manual smoke possible | No GitHub Actions, no pytest/Jest |

---

## 3. Not implemented (do not document as done)

- Online payment **gateway** (cards captured in-app, Razorpay, Stripe, webhooks)
- QR / biometric attendance hardware
- Workout programs, exercise logs, dietitian plan builder
- Body measurement history over time (height/weight exist on Member only as current fields)
- Push/email/SMS reminders
- Staff UI to review other members’ food logs
- Traditional computer-vision models (YOLO, custom CNN) — nutrition uses an LLM or mock
- USDA / IFCT nutrition lookup tables
- Automated test suite and CI/CD pipelines beyond hosting build commands
- httpOnly cookie auth
- Multi-gym / multi-tenant

---

## 4. Known limitations

See also Chapter 15 in the technical documentation.

| Area | Current status | Limitation | Suggested improvement |
|---|---|---|---|
| Tests | None in repo | Regressions are easy | Add pytest + DRF API tests; optional Playwright |
| Tokens | localStorage | XSS can steal JWTs | httpOnly cookies or BFF |
| Food AI | LLM estimates | Dish names and portions can be wrong; no food DB | Human confirm (already required) + optional reference tables |
| Groq/HF rate limits | Not wrapped | HTTP 429 surfaces as generic errors | Map 429 to a clear message + backoff |
| Scan photos | Discarded | Cannot audit what the model saw | Optional encrypted short-TTL storage |
| Summary API | Omits fiber | UI cannot chart fiber from summary | Add `fiber_g` to daily aggregation |
| Payments | Manual records | Not online checkout | Keep as records; do not imply PCI payments |
| Member delete | PROTECT on payments | Cannot delete members with payment history | Already documented: mark inactive |
| Seed passwords | Public in README | Unsafe if left on a public URL | Disable seed after first deploy |
| Trainer UI | Incomplete vs API | Trainers cannot manage trainer directory | Intentional or add a “my profile” page |
| Nutrition admin | Missing | Hard to inspect scans in Django admin | Register models |

---

## 5. Future enhancements (not built)

These are reasonable next steps, **not** current features:

- Staff/trainer nutrition monitoring UI
- Persist or hash meal photos for support/audit
- Workout plans and diet plans
- Body measurement timeline
- QR check-in
- Automated expiry reminders
- Richer analytics
- Automated tests and CI
- Stricter production security headers / rate limiting

Member self-service portal and AI calorie tracking are **already started** (portal + nutrition). Remaining work is depth (staff views, tests, accuracy), not a green-field portal.

---

## 6. Current implementation status (one paragraph)

FitTrack is a working gym operations SPA + REST API: members, trainers, plans, membership sales/renewals, desk payment records, attendance, role-based dashboards, a member portal, and an optional vision-LLM food log with consent and human confirmation. Payments are bookkeeping, not a payment processor. Nutrition accuracy depends on the configured model. Automated tests and staff nutrition UI are absent. Deployment support is configured for Render (API), Cloudflare Pages (frontend), and Supabase PostgreSQL; local development retains MySQL support. A Vercel config remains as an optional frontend alternative.
