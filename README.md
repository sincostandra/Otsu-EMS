# Otsu EMS

Employee Management System — a Django + DRF API with a React (Vite) single-page
frontend. Admins manage employees and monitor attendance; employees check in/out
and track their own monthly stats. Lateness is derived from check-in time
(work starts 09:00, 15-minute grace), so a check-in after 09:15 counts as **Telat**.

## Features

- **Auth** — JWT (email as username), role-based access (admin vs. employee).
- **Employees** — full CRUD, pagination, search, filter by jabatan/status (admin only).
- **Attendance** — self check-in/out, derived on-time/late status, admin overview with filters.
- **Reports** — admin dashboard (today's late list, per-jabatan mix, 7-day recap chart);
  employee self-stats (monthly hadir / telat / tidak hadir / attendance rate).
- **Export** — employees and attendance to CSV / Excel (admin only).

## Tech stack

| Layer     | Choice |
|-----------|--------|
| Backend   | Django 5.2, Django REST Framework, SimpleJWT, django-filter |
| Frontend  | React 19, Vite, react-router, axios, Chart.js |
| Database  | SQLite (dev) · PostgreSQL (prod, via `DATABASE_URL`) |
| Static    | WhiteNoise serves the built SPA (single-container, same-origin) |
| Server    | Gunicorn |
| Tooling   | pytest, ruff (backend) · oxlint (frontend) · GitHub Actions CI |

## Architecture

One container serves everything on a single origin: Django exposes the API under
`/api/`, WhiteNoise serves the built React bundle under `/static/`, and a catch-all
route returns `index.html` so client-side routing works on deep links. The frontend
calls the API with a relative `baseURL` (`/api`), so no CORS is needed in production.

## Quick start (Docker)

Runs the full production-like stack (Gunicorn + WhiteNoise + Postgres):

```bash
docker compose up --build
```

Then open http://localhost:8000. The container migrates and seeds the demo data on
first boot (`RUN_SEED=1` in `docker-compose.yml`).

## Local development

Two processes; Vite proxies `/api` to Django (see `frontend/vite.config.js`).

**Backend** (from `backend/`):

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # demo workforce + attendance
python manage.py runserver        # http://localhost:8000
```

**Frontend** (from `frontend/`):

```bash
npm install
npm run dev                       # http://localhost:5173
```

## Demo credentials

Created by `python manage.py seed_demo` (passwords are the local defaults; override
with the `SEED_*` env vars).

| Role     | Email             | Password        |
|----------|-------------------|-----------------|
| Admin    | admin@otsu.test   | `admin12345`    |
| Employee | budi@otsu.test    | `employee12345` |
| Employee | citra@otsu.test   | `employee12345` |
| Employee | eko@otsu.test     | `employee12345` |

The seed creates ~300 employees with ~30 days of varied attendance; only the accounts
above have usable passwords — everyone else gets a random one. Re-run with `--reset`
to rebuild from scratch.

## Environment variables

| Variable                 | Default                     | Notes |
|--------------------------|-----------------------------|-------|
| `DJANGO_SECRET_KEY`      | insecure dev key            | Set a real secret in prod |
| `DJANGO_DEBUG`           | `True`                      | `0` in prod |
| `DJANGO_ALLOWED_HOSTS`   | `localhost,127.0.0.1`       | Comma-separated |
| `CSRF_TRUSTED_ORIGINS`   | empty                       | Comma-separated, full origins |
| `DATABASE_URL`           | SQLite                      | `postgres://…` switches to Postgres |
| `RUN_SEED`               | `0`                         | `1` seeds on container boot |
| `SEED_ADMIN_EMAIL`       | `admin@otsu.test`           | Seed admin login |
| `SEED_ADMIN_PASSWORD`    | `admin12345`                | Seed admin password |
| `SEED_EMPLOYEE_PASSWORD` | `employee12345`             | Demo employees' password |
| `WEB_CONCURRENCY`        | `2`                         | Gunicorn workers |

On Railway, `DATABASE_URL`, `PORT`, and the public hostname
(`RAILWAY_PUBLIC_DOMAIN`) are injected automatically; set the rest in the
service variables (see Deployment).

## API reference

All endpoints are under `/api/` and require a `Bearer` token except login.

| Method | Endpoint                        | Description |
|--------|---------------------------------|-------------|
| POST   | `/api/auth/login/`              | Obtain access + refresh tokens |
| POST   | `/api/auth/refresh/`            | Refresh access token |
| GET    | `/api/auth/me/`                 | Current user |
| GET/POST | `/api/employees/`             | List (paginated/searchable) / create *(admin)* |
| GET/PUT/DELETE | `/api/employees/{id}/`  | Retrieve / update / delete *(admin)* |
| GET    | `/api/employees/jabatan-options/` | Distinct jabatan for filters |
| GET    | `/api/employees/export/?format=csv\|xlsx` | Export *(admin)* |
| GET    | `/api/attendance/`              | List (role-scoped) |
| POST   | `/api/attendance/check-in/`     | Check in |
| POST   | `/api/attendance/check-out/`    | Check out |
| GET    | `/api/attendance/export/?format=csv\|xlsx` | Export *(admin)* |
| GET    | `/api/reports/summary/`         | Admin dashboard data |
| GET    | `/api/reports/my-stats/`        | Employee's own monthly stats |

## Testing

```bash
cd backend
pytest              # 35 tests
ruff check .        # lint

cd ../frontend
npm run lint
npm run build
```

CI (`.github/workflows/ci.yml`) runs the same checks on every PR to `main`.

## Deployment (Railway)

The repo ships a `railway.json` so Railway builds straight from the `Dockerfile`.

1. **Create the project** — in Railway: **New Project → Deploy from GitHub repo →
   select this repo**. Railway detects the `Dockerfile` and builds it.
2. **Add Postgres** — in the project canvas: **New → Database → Add PostgreSQL**.
3. **Connect the database** — on the web service, add a `DATABASE_URL` variable
   pointing at the Postgres service (its `DATABASE_URL` connection string). This is
   what selects managed Postgres; without it the app falls back to local SQLite.
4. **Set the service variables** (Variables tab on the web service):
   - `DJANGO_SECRET_KEY` — a long random string
   - `DJANGO_DEBUG=0`
   - `RUN_SEED=1` for the first deploy, then set it to `0` so later deploys skip re-seeding
   - `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`, `SEED_EMPLOYEE_PASSWORD` — demo logins
   `PORT` and `RAILWAY_PUBLIC_DOMAIN` (used for `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`)
   are provided by Railway; no need to set them.
5. **Expose the service** — under **Settings → Networking → Generate Domain** to get
   a public `*.up.railway.app` URL.

The entrypoint migrates (and optionally seeds) before Gunicorn binds to `$PORT`.

## Project structure

```
Otsu-EMS/
├── backend/            # Django project (config) + apps: accounts, employees, attendance, reports
│   ├── config/         # settings, urls, SPA-serving view, wsgi
│   └── entrypoint.sh   # migrate → optional seed → gunicorn
├── frontend/           # React (Vite) SPA
├── Dockerfile          # multi-stage: build SPA → serve via Django/WhiteNoise
├── docker-compose.yml  # local prod-like stack (web + Postgres)
└── railway.json        # Railway deploy config (builds from Dockerfile)
```
