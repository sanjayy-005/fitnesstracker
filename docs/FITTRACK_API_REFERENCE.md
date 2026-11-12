# FitTrack – API Reference

Base URL locally: `http://127.0.0.1:8000/api`

All paths below are relative to `/api` unless noted. Django admin is `http://127.0.0.1:8000/admin/` (session auth, not JWT).

**Authentication:** `Authorization: Bearer <access_token>` except login, token refresh, and health.

**Roles:** `ADMIN`, `STAFF`, `TRAINER`, `MEMBER`.

**Pagination** (list endpoints that use the default pager):

```json
{ "count": 57, "next": "http://.../?page=2", "previous": null, "results": [ ] }
```

Query: `page`, `page_size` (max 100, default 10). Search: `search`. Ordering: `ordering`.

**Errors:** DRF-style `{ "detail": "..." }` or field maps `{ "email": ["..."] }`. Protected deletes return **409** (`core/exceptions.py`).

This catalogue matches `backend/config/urls.py` and the app URL modules. It does not invent endpoints.

---

## 1. Health

### GET `/health/`

| | |
|---|---|
| Auth | None |
| Roles | Public |
| Purpose | Process + database ping for Render |

**200**

```json
{ "status": "ok", "database": "up" }
```

**503** if the database query fails: `{ "status": "error", "database": "down" }`

---

## 2. Authentication (`/auth/`)

### POST `/auth/login/`

Auth: none.

Body:

```json
{ "username": "admin", "password": "Admin@123" }
```

**200**

```json
{
  "access": "<jwt>",
  "refresh": "<jwt>",
  "user": {
    "id": 1,
    "username": "admin",
    "first_name": "",
    "last_name": "",
    "full_name": "admin",
    "email": "",
    "phone": "",
    "role": "ADMIN",
    "member_id": null,
    "is_active": true,
    "last_login": "...",
    "date_joined": "..."
  }
}
```

Member logins include `member_id` when a `Member` row is linked.

**401** invalid credentials.

### POST `/auth/refresh/`

Auth: none (body token). SimpleJWT default.

```json
{ "refresh": "<refresh jwt>" }
```

**200** `{ "access": "...", "refresh": "..." }` because rotation is enabled.

**401** expired or blacklisted refresh.

### POST `/auth/logout/`

Auth: any authenticated user.

```json
{ "refresh": "<refresh jwt>" }
```

Blacklists the refresh token. Missing/invalid refresh still returns **200** `{ "detail": "Logged out successfully." }`.

### GET `/auth/me/`

Auth: any authenticated user. Returns `UserSerializer` (same `user` object as login).

---

## 3. Users (admin)

Router: `/auth/users/`

| Method | Path | Roles |
|---|---|---|
| GET | `/auth/users/` | ADMIN |
| POST | `/auth/users/` | ADMIN |
| GET | `/auth/users/{id}/` | ADMIN |
| PATCH/PUT | `/auth/users/{id}/` | ADMIN |
| DELETE | `/auth/users/{id}/` | ADMIN (not self) |

Filters: `role`, `is_active`. Search: username, names, email.

Create body (typical):

```json
{
  "username": "desk2",
  "password": "A-strong-password1",
  "first_name": "Ravi",
  "last_name": "Kumar",
  "email": "ravi@example.com",
  "phone": "9876543210",
  "role": "STAFF",
  "is_active": true
}
```

Cannot create `TRAINER` or `MEMBER` here (those logins are created from Trainers / Members). Cannot deactivate or change role of your own account. Cannot delete yourself.

---

## 4. Members

| Method | Path | Read / write |
|---|---|---|
| GET | `/members/` | ADMIN, STAFF, TRAINER (trainers: assigned members only) |
| POST | `/members/` | ADMIN, STAFF |
| GET | `/members/{id}/` | same as list |
| PATCH | `/members/{id}/` | ADMIN, STAFF |
| DELETE | `/members/{id}/` | ADMIN, STAFF — also deletes linked `User` if any. Fails **409** if payments exist (`PROTECT`) |

Filters: `membership_status` (`ACTIVE` \| `EXPIRING` \| `EXPIRED` \| `NONE`), `trainer`, `trainer_isnull`, `is_active`, `gender`. Search: name, email, phone, `member_code`.

Optional login fields on create/update: `username`, `password`.

**Example list item (fields from `MemberSerializer`):** `id`, `member_code`, `full_name`, `email`, `phone`, `gender`, `gender_display`, `date_of_birth`, `address`, emergency contacts, `height_cm`, `weight_kg`, `trainer`, `trainer_name`, `joined_date`, `is_active`, `notes`, `membership_status`, `membership_plan`, `membership_end_date`, `days_left`, `login_username`, `created_at`.

---

## 5. Trainers

| Method | Path | Roles |
|---|---|---|
| GET | `/trainers/` | ADMIN, STAFF, TRAINER |
| POST | `/trainers/` | ADMIN |
| GET/PATCH/PUT/DELETE | `/trainers/{id}/` | write ADMIN; delete also removes linked login |
| GET | `/trainers/{id}/members/` | ALL staff roles; trainer only if it is themselves |
| POST | `/trainers/{id}/assign/` | ADMIN, STAFF |
| POST | `/trainers/{id}/unassign/` | ADMIN, STAFF |

Assign body:

```json
{ "member_ids": [1, 2, 3] }
```

**200** `{ "assigned": 3, "detail": "..." }`

Cannot assign to an inactive trainer.

---

## 6. Plans

| Method | Path | Roles |
|---|---|---|
| GET | `/plans/` | ADMIN, STAFF, TRAINER |
| POST/PATCH/DELETE | `/plans/` | ADMIN |

Fields: `name` (unique), `plan_type` (`MONTHLY` 30 days, `QUARTERLY` 90, `YEARLY` 365), `price`, `description`, `features` (newline-separated; response also `features_list`), `is_active`, `active_members`, `duration_days`.

Deleting a plan that has memberships is **blocked** (`PROTECT` on `Membership.plan`).

---

## 7. Memberships

No PATCH. Create, list, retrieve, delete (admin), plus actions.

| Method | Path | Roles |
|---|---|---|
| GET | `/memberships/` | ADMIN, STAFF, TRAINER (own members) |
| POST | `/memberships/` | ADMIN, STAFF |
| GET | `/memberships/{id}/` | same as list |
| DELETE | `/memberships/{id}/` | ADMIN |
| POST | `/memberships/{id}/renew/` | ADMIN, STAFF |
| POST | `/memberships/{id}/cancel/` | ADMIN, STAFF |

**Sell**

```json
{
  "member": 1,
  "plan": 2,
  "start_date": "2026-11-12",
  "record_payment": true,
  "payment_method": "UPI",
  "amount": 2200
}
```

`start_date` optional; cannot be in the future. If omitted and an active membership exists, start is the day after that end date (`plans/services.py`).

**Renew** — `plan` optional (same plan). Payment options same as sell.

**Cancel** — only if `effective_status` is ACTIVE. Sets `status=CANCELLED`.

Response uses **effective** status (expired by date even if the row still says ACTIVE until `sync_expired` runs).

---

## 8. Payments (records)

Trainers and members **cannot** call these endpoints (`read_roles` / `write_roles` = ADMIN, STAFF).

| Method | Path | Notes |
|---|---|---|
| GET | `/payments/` | Filters via `PaymentFilter` (status, method, dates — see `payments/filters.py`) |
| POST | `/payments/` | Sets `received_by` to current user |
| GET/PATCH | `/payments/{id}/` | |
| DELETE | `/payments/{id}/` | ADMIN |
| GET | `/payments/summary/` | Totals for current filters |
| GET | `/payments/{id}/receipt/` | Print payload + gym settings |

**Summary 200**

```json
{
  "total_collected": 14000.0,
  "total_pending": 0.0,
  "total_refunded": 0.0,
  "count": 12
}
```

Methods: `CASH`, `CARD`, `UPI`, `BANK_TRANSFER`. Statuses: `PAID`, `PENDING`, `REFUNDED`.

This is **not** a payment-processor API. There are no capture, webhook, or refund-gateway endpoints.

---

## 9. Attendance

| Method | Path | Roles |
|---|---|---|
| GET | `/attendance/` | ADMIN, STAFF, TRAINER (scoped) |
| GET | `/attendance/{id}/` | same |
| DELETE | `/attendance/{id}/` | ADMIN, STAFF |
| POST | `/attendance/check-in/` | ADMIN, STAFF, TRAINER |
| POST | `/attendance/{id}/check-out/` | same |
| GET | `/attendance/report/` | same; `?days=30` (1–365) |

**Check-in**

```json
{ "member": 12 }
```

Validations: member active; trainer assignment if caller is TRAINER; active membership; one check-in per calendar day.

**Check-out:** only for today’s record; not already checked out.

Report includes `daily`, `top_members` (5), `peak_hours` (hours 5–22), `total_visits`, `unique_members`, `average_per_day`.

---

## 10. Dashboard

### GET `/dashboard/`

Roles: **ADMIN, STAFF, TRAINER** only (`STAFF_ROLES`). Members receive **403**.

Trainers get member/attendance stats for assigned members. `can_view_finance` is true only for ADMIN and STAFF. Finance keys (`finance`, `monthly_revenue`, `revenue_by_method`, `recent_payments`) are **omitted** for trainers.

---

## 11. Member portal (`/portal/`)

All require `MemberPortalPermission`: role `MEMBER`, active linked `member_profile`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/portal/profile/` | Name, code, contact, trainer_name, consent timestamp, current membership |
| GET | `/portal/memberships/` | All memberships for that member |
| GET | `/portal/attendance/` | Paginated visits |

No portal write endpoints except nutrition consent (under `/nutrition/consent/`).

---

## 12. Nutrition

Roles for scans/entries/summary: ADMIN, STAFF, TRAINER, MEMBER (`STAFF_AND_MEMBER`). Members always scoped to themselves. Trainers scoped to assigned members. Staff/admin pass `member` when acting for someone else.

### POST `/nutrition/consent/`

Roles: **MEMBER** only.

**200** `{ "nutrition_consent_at": "<iso datetime>" }`

### GET `/nutrition/status/`

Roles: ADMIN, STAFF.

```json
{
  "enabled": true,
  "configured": true,
  "provider": "mock",
  "model": "Qwen/Qwen2.5-VL-7B-Instruct",
  "pending_scans": 0,
  "provider_healthy": true
}
```

### POST `/nutrition/scans/`

`multipart/form-data`: `image` (JPEG/PNG/WebP, ≤ 5 MB), optional `meal_type`, `note`, `member` (staff/trainer).

**201** `FoodScanSerializer`: `id`, `member`, `member_name`, `meal_type`, `note`, `status` (`PENDING` is brief; response is after analysis: `SUCCEEDED` \| `NEEDS_REVIEW` \| `FAILED`), `analysis`, `error`, `latency_ms`, `model_name`, timestamps.

`analysis` shape (Pydantic `FoodAnalysis`):

```json
{
  "is_food": true,
  "warnings": ["..."],
  "items": [
    {
      "name": "Steamed White Rice",
      "local_name": "Chawal",
      "quantity": 1,
      "unit": "plate",
      "estimated_grams": 200,
      "calories_kcal": 260,
      "protein_g": 5,
      "carbs_g": 56,
      "fat_g": 0.5,
      "fiber_g": 0.5,
      "confidence": "high",
      "assumptions": "..."
    }
  ]
}
```

**400** no consent, inactive member, daily limit, bad image. **503** scanning disabled or missing API key.

### GET `/nutrition/scans/` and `/nutrition/scans/{id}/`

Query `member` for admin/staff.

### POST `/nutrition/scans/{id}/confirm/`

JSON:

```json
{
  "eaten_on": "2026-11-12",
  "meal_type": "LUNCH",
  "edited": true,
  "items": [
    {
      "name": "Rice",
      "quantity": 1,
      "unit": "plate",
      "grams": 200,
      "kcal": 260,
      "protein_g": 5,
      "carbs_g": 56,
      "fat_g": 0.5,
      "fiber_g": 0.5,
      "confidence": "high",
      "was_edited": false
    }
  ]
}
```

**201** `MealEntrySerializer` including `items`. Fails if scan is FAILED or already confirmed.

### GET `/nutrition/entries/`

Query: `member`, `date_from`, `date_to`.

### GET `/nutrition/entries/{id}/`

### DELETE `/nutrition/entries/{id}/`

ADMIN, STAFF only (`action_roles.destroy`).

### POST `/nutrition/entries/manual/`

Same item list as confirm; optional `member`. Source stored as `MANUAL`.

### GET `/nutrition/summary/?days=7`

Members: own data. Others: require `member`. `days` 1–90.

```json
{
  "member": 1,
  "days": 7,
  "today_kcal": 320.0,
  "daily": [
    { "date": "2026-11-12", "kcal": 320.0, "protein_g": 14.0, "carbs_g": 48.0, "fat_g": 8.0 }
  ]
}
```

Fiber is **not** in this payload (limitation).

---

## 13. Common HTTP statuses

| Status | When |
|---|---|
| 200/201 | Success |
| 400 | Validation |
| 401 | Missing/invalid JWT |
| 403 | Authenticated but wrong role or trainer scope |
| 404 | Missing object |
| 409 | Protected FK delete |
| 415 | Wrong content type (should not occur on confirm after parser split) |
| 429 | Possible from **upstream** LLM; Django does not define a project-wide throttle |
| 503 | Health DB down, or food AI not configured |

---

## 14. Example session (staff)

```bash
# Login
curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"staff","password":"Staff@123"}'

# Members (replace TOKEN)
curl -s http://127.0.0.1:8000/api/members/?page=1 \
  -H 'Authorization: Bearer TOKEN'

# Check-in
curl -s -X POST http://127.0.0.1:8000/api/attendance/check-in/ \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"member":1}'
```

Demo passwords above are public seed values, not production secrets.
