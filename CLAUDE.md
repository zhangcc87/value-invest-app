# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A fork of the [tiangolo full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template), adapted to a **Vue 3 + Element Plus** frontend that is deployed separately from the API. The repo's own docs (`README.md`, `development.md`, `deployment*.md`, `backend/README.md`) have been updated to match.

- **Backend**: FastAPI + SQLModel + PostgreSQL + Alembic, JWT auth, emails via React Email → Jinja templates.
- **Frontend**: **Vue 3 + TypeScript + Vite + Element Plus** (upstream used React + shadcn/ui).
- The frontend is **deployed separately** (its own nginx container); the backend no longer serves it.

## Divergences from the upstream template (important)

- The frontend is Vue 3 / Element Plus, not React. `frontend/src/` holds the app: `api/request.ts` (axios), `router/index.ts`, `layouts/MainLayout.vue`, `views/*.vue`.
- `backend/app/main.py` has the `app.frontend(...)` mount **commented out** — FastAPI serves the API only, and `backend/Dockerfile` does not build a frontend.
- Frontend build output is `frontend/dist` (Vite default), served by `frontend/nginx.conf` (its own nginx image).
- Package manager at the root is **bun** (workspaces: `frontend`, `packages/*`), but `bun` is **not installed locally** — invoke it via `npx -y bun@1.3.12 <cmd>` (that is how `bun.lock` is regenerated). The `frontend/Dockerfile` uses `npm` internally.
- Backend model domain is still the template's `User` / `Item` (`backend/app/models/tables.py`); the "value-invest" domain has not been modeled yet.
- **Deployment routing:** Traefik routes the domain to the `frontend` service (nginx), which serves the static files and proxies `/api/v1`, `/docs`, and `/redoc` to the `backend` service. The backend has no Traefik router and is internal-only. See `compose.yml` and `frontend/nginx.conf`.

## Commands

Run backend commands from `./backend/`; run frontend/root commands from the repo root. The backend reads its settings from the **top-level** `.env` (`env_file="../.env"` in `backend/app/core/config.py`).

### Local development
```bash
docker compose up -d db mailpit          # start Postgres + Mailpit only

# backend (from ./backend)
uv sync
uv run bash scripts/prestart.sh          # alembic upgrade head + seed initial data
uv run fastapi dev                       # http://localhost:8000, docs at /docs

# frontend (from repo root)
bun install
bun run dev                              # Vite dev server at http://localhost:5173
```

### Tests
```bash
# from ./backend
uv run bash scripts/test.sh              # coverage + pytest tests/ ; writes htmlcov/
uv run pytest tests/test_users.py::test_get_users   # single test
uv run pytest tests/ -x                  # stop on first failure
```
Tests need a running database (`docker compose up -d db`). The default `User`/`Item` fixtures live in `backend/tests/`.

The suite runs against a **dedicated test database** (`TEST_DATABASE_URL`, default `app_test` in the root `.env`), not the dev database — `tests/conftest.py` overrides `get_db`, creates the schema from `SQLModel.metadata`, and truncates only the test DB. If `TEST_DATABASE_URL` is unset the suite fails fast. Create the database once:
```bash
docker compose exec db psql -U postgres -d postgres -c "CREATE DATABASE app_test"
```
(Schema is created per run by the `db` fixture; no `alembic upgrade` needed on the test DB.)

### Lint / format / typecheck
```bash
# backend, from ./backend
bash scripts/lint.sh                     # mypy + ty + ruff check + ruff format --check

# repo-wide pre-commit (from root)
uv run prek install -f                   # install git hook
uv run prek run --all-files
```
Backend linting is strict: mypy `strict = true`, ruff with `T201` (no `print()` statements). Frontend type checking runs through `npm --prefix frontend run lint` (the `frontend` package's `lint` script is `vue-tsc -b`), wired into pre-commit as the `local-frontend-typecheck` hook.

### Migrations
```bash
# from ./backend
uv run alembic revision --autogenerate -m "message"   # after changing app/models/
uv run alembic upgrade head
```

### Full stack via Docker Compose
```bash
docker compose run --rm backend bash scripts/prestart.sh
docker compose watch
```
App via Traefik: http://localhost:8000 (backend) · http://localhost:8080 (frontend nginx) · Adminer http://localhost:8081 · Traefik UI http://localhost:8090 · Mailpit http://localhost:8025. Stop any locally running `uv run fastapi dev` first — both use port 8000.

## Architecture

### Auth flow
- Login: `POST /api/v1/login/access-token` with `application/x-www-form-urlencoded` body `username=<email>&password=<password>` (OAuth2 form, not JSON). Returns `{access_token, token_type}`.
- Frontend stores the token in `localStorage.token`; `frontend/src/api/request.ts` adds the `Bearer` header and, on any 401, clears the token and redirects to `/login`.
- `frontend/src/router/index.ts` has a global guard: no token + any non-`/login` route → redirect to `/login`.
- Backend deps (`backend/app/api/deps.py`): `SessionDep` (DB session), `CurrentUser`, `get_current_active_superuser`. User-management endpoints require superuser.

### Backend layout
The backend is layered: **`api` → `services` → `repositories`**. Keep the layers separate when adding code.
- `backend/app/api/routes/` — thin HTTP layer: param validation + call a service + return. `login.py`, `users.py`, `items.py`, `utils.py`, and `private.py` (only mounted when `FASTAPI_ENV == "development"`; see `backend/app/api/main.py`). Routes must **not** call `session.commit()`.
- `backend/app/services/` — business logic and the **transaction boundary** (the only layer that calls `session.commit()`). `user.py`, `auth.py`, `item.py`, `email.py` (React-Email/Jinja rendering + sending), `seed.py` (initial data).
- `backend/app/repositories/` — pure DB access (`add`/`flush`/`refresh`, queries). **Never commits**, never raises HTTP.
- `backend/app/models/` — SQLModel **table** models (`table=True`): `tables.py` (`User` + `Item`), `base.py` (`get_datetime_utc`). `User` and `Item` must stay in the **same module** (bidirectional `Relationship` breaks if split across files with SQLModel). `models/__init__.py` re-exports `SQLModel` + the table models for alembic.
- `backend/app/schemas/` — pydantic DTOs (no `table=True`): `user.py`, `item.py`, `token.py`. Schemas must not import `models`.
- `backend/app/core/` — `config.py` (settings), `db.py` (engine only), `security.py`.
- `backend/app/api/main.py` picks the health-check and routes; all routes are under `settings.API_V1_STR` (`/api/v1`).
- Users list is paginated with **`?page=` and `?size=` query params** (not `skip`/`limit`) and returns `{data, count}`.

### Frontend ↔ backend contract
- Dev: `frontend/.env.development` sets `VITE_API_URL=http://localhost:8000/api/v1`.
- Prod: `frontend/.env.production` sets `VITE_API_URL=/api/v1`, and `frontend/nginx.conf` proxies `/api/v1` (plus `/docs` and `/redoc`) to `http://backend:8000`.
- `frontend/src/api/request.ts` sets `baseURL` from `VITE_API_URL` and unwraps `res.data`, so view code calls e.g. `request.get("/users/me")` and receives the payload directly (not an axios response).
- The `@` alias maps to `frontend/src` (see `frontend/vite.config.ts`).

### Config
- `backend/app/core/config.py` (`Settings`) loads the root `.env`. `DATABASE_URL` and `TEST_DATABASE_URL` are rewritten to use the `psycopg` driver. Default `changethis` secrets only warn in `development` and raise otherwise.

## Conventions

- Comments and UI strings in the frontend are in Chinese; match that style when editing frontend files.
- Keep the backend layered: table models in `backend/app/models/`, DTOs in `backend/app/schemas/`, DB access in `backend/app/repositories/`, business logic in `backend/app/services/`, and endpoints in `backend/app/api/routes/`. Routes stay thin (no `session.commit()`); repositories never commit.
