# Value Invest App - Development

## Local Development

For local development, run PostgreSQL and Mailpit with Docker Compose, and run the FastAPI and Vite development servers locally.

Start the supporting services:

```bash
docker compose up -d db mailpit
```

Then, from the `backend` directory, install the dependencies and prepare the database:

```bash
uv sync
uv run bash scripts/prestart.sh
```

Start the FastAPI development server:

```bash
uv run fastapi dev
```

In another terminal, from the project root, install the frontend dependencies and start the Vite development server:

```bash
bun install
bun run dev
```

Now you can open these URLs:

- Frontend development server: <http://localhost:5173>
- Backend API: <http://localhost:8000>
- Interactive API documentation (Swagger UI): <http://localhost:8000/docs>
- Mailpit: <http://localhost:8025>

The frontend development server calls the backend at `http://localhost:8000`, as configured in `frontend/.env.development` (`VITE_API_URL`).

## Frontend Build

The frontend is a standalone Vue app; the backend no longer serves it.

Build it from the `frontend` directory:

```bash
bun run build
```

The build (type-check with `vue-tsc` + Vite) is written to `frontend/dist`. In production it is served by nginx via `frontend/Dockerfile` and `frontend/nginx.conf`, which also proxies `/api/v1` to the backend. For production, `frontend/.env.production` sets `VITE_API_URL=/api/v1`, so the browser talks to the same origin and nginx forwards API calls to the backend.

## Full Stack with Docker Compose

To run the backend and the built frontend in Docker Compose:

```bash
docker compose run --rm backend bash scripts/prestart.sh
docker compose watch
```

Now you can open these URLs:

- Frontend (nginx): <http://localhost:8080>
- Backend API: <http://localhost:8000>
- Interactive API documentation (Swagger UI): <http://localhost:8000/docs>
- Adminer, database web administration: <http://localhost:8081>
- Traefik UI, to see how the routes are being handled by the proxy: <http://localhost:8090>
- Mailpit: <http://localhost:8025>

Stop a locally running FastAPI server before starting the Compose backend because both use port `8000`.

**Note**: The first time you start the stack, it might take a minute for all the services to be ready. To monitor it, use `docker compose logs`, or `docker compose logs backend` for the backend service.

## Mailpit

[Mailpit](https://mailpit.axllent.org) captures emails sent during local development instead of delivering them. The local backend connects to it at `localhost:1025`, and the Compose backend connects to the `mailpit` service. Captured emails are available at <http://localhost:8025>.

## Docker Compose Files and Environment Variables

The main `compose.yml` file contains the configuration shared by the whole stack. Docker Compose loads it automatically.

The `compose.override.yml` file adds local development settings, such as published ports and mounting the source code as a volume. Docker Compose also loads it automatically and applies it on top of `compose.yml`.

The `compose.deploy.yml` file contains the deployment-specific settings, including HTTPS and automatic certificate handling. It is explicitly combined with `compose.yml` when deploying the application.

The backend reads local settings from the `.env` file. Docker Compose also uses it for variable interpolation and passes the settings each container needs.

After changing variables, make sure you restart the stack:

```bash
docker compose watch
```

## The `.env` File

The tracked `.env` file contains local development defaults, passwords, and other configuration. Its hostnames use `localhost` for processes running on your machine. Docker Compose overrides hostnames such as the database and SMTP server with their Compose service names.

Do not store deployment secrets in `.env`. Configure them as described in the [FastAPI Cloud deployment guide](./deployment.md) or the [Docker Compose deployment guide](./deployment-docker-compose.md).

## Pre-commit Hooks and Code Linting

The project uses [prek](https://prek.j178.dev/), a modern alternative to [pre-commit](https://pre-commit.com/), for code linting and formatting.

You can find a file `.pre-commit-config.yaml` with configurations at the root of the project.

### Install `prek` to Run Automatically

`prek` is already part of the dependencies of the project.

From the project root, install the Git hook so that `prek` runs automatically before each commit:

```bash
uv run prek install -f
```

The `-f` flag forces the installation, in case there was already a `pre-commit` hook previously installed.

Now whenever you try to commit, for example with:

```bash
git commit
```

`prek` will check and format the code you are about to commit. If it modifies any files, add those files to Git again before committing.

### Run `prek` Manually

You can also run `prek` manually on all files from the project root:

```bash
uv run prek run --all-files
```

### What Runs

- **Backend**: `ruff check`, `ruff format`, `mypy`, and `ty` over `backend/app`.
- **Frontend**: `vue-tsc -b` (type check) via `npm --prefix frontend run lint` when files under `frontend/` change.
- **Other**: typos, YAML/TOML checks, end-of-file and trailing-whitespace fixers.
