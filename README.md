# Value Invest App

A full-stack application with a **FastAPI** backend API and a **Vue 3** single-page
frontend, wired together with Docker Compose. The frontend is deployed separately
(static files served by nginx); the backend serves the API only.

## Technology Stack

**Backend**

- ⚡ [FastAPI](https://fastapi.tiangolo.com) for the REST API.
  - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for models and database access.
  - 🔍 [Pydantic](https://docs.pydantic.dev) for validation and settings.
  - 💾 [PostgreSQL](https://www.postgresql.org) as the database.
  - 🐘 [Alembic](https://alembic.sqlalchemy.org) for migrations.
- 🔑 JWT authentication and secure password hashing.
- 📫 Email sending over SMTP (templates authored with [React Email](https://react.email) and rendered as Jinja HTML).
- ✅ Tests with [Pytest](https://pytest.org).

**Frontend**

- 🚀 [Vue 3](https://vuejs.org) + TypeScript + [Vite](https://vitejs.dev).
- 🎨 [Element Plus](https://element-plus.org) components, with light/dark themes.
- 🧭 `vue-router` with an auth guard; `axios` client that attaches the JWT.
- 📦 Built to static files and served by nginx (its own container), independently of the API.

**Tooling**

- 🐋 [Docker Compose](https://docs.docker.com) for local services and deployment.
  - 📞 [Traefik](https://traefik.io) as a reverse proxy with automatic HTTPS (deployment).
- 📦 [uv](https://docs.astral.sh/uv/) for Python; [bun](https://bun.sh) workspaces for JavaScript.
- ✅ Linting/formatting via [prek](https://prek.j178.dev/) (pre-commit), ruff, mypy, ty, and `vue-tsc`.
- 📬 [Mailpit](https://mailpit.axllent.org) for local email testing during development.

## Getting Started

Start the supporting services and run the two dev servers side by side. See
[development.md](./development.md) for the full walkthrough.

```bash
# 1. Supporting services
docker compose up -d db mailpit

# 2. Backend (from ./backend)
uv sync
uv run bash scripts/prestart.sh
uv run fastapi dev                   # http://localhost:8000

# 3. Frontend (from the repo root)
bun install
bun run dev                          # http://localhost:5173
```

- Interactive API docs (Swagger UI): <http://localhost:8000/docs>
- Frontend dev server: <http://localhost:5173>
- Mailpit (captured emails): <http://localhost:8025>

## Documentation

- Backend: [backend/README.md](./backend/README.md)
- Development: [development.md](./development.md)
- Deployment to FastAPI Cloud: [deployment.md](./deployment.md)
- Self-hosted deployment with Docker Compose: [deployment-docker-compose.md](./deployment-docker-compose.md)

## License

MIT — see [LICENSE](./LICENSE).
