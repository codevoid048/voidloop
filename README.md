# Void Loop

Most habit apps want to be your coach. Void Loop is closer to a personal desk - habits, tasks, and notes in one place, without the noise.

You check in on habits. You plan the day. You keep notes that actually stick around. That’s the loop.

Registration is invite-only. If you’re running your own instance, you create an admin, send invites, and decide who gets in.

---

## Stack


| Piece     | What                                                                             |
| --------- | -------------------------------------------------------------------------------- |
| `client/` | Next.js (App Router)                                                             |
| `server/` | Django + Django Ninja (JWT)                                                      |
| Deploy    | Amplify (frontend), Lambda + API Gateway (backend), Terraform in `server/infra/` |


---



## Local setup

You’ll want two terminals. Python **3.12+**, [uv](https://github.com/astral-sh/uv), Node **20+**, and [pnpm](https://pnpm.io).

### Backend

```bash
cd server
cp .env.example .env
uv sync
make migrate
uv run python src/manage.py createsuperuser
make run
```

API: `http://127.0.0.1:8000`  
Docs: `http://127.0.0.1:8000/api/v1/docs`

SQLite is fine for local. For Postgres, set `DATABASE_URL` in `.env`.

Turnstile uses Cloudflare’s always-pass test keys in `.env.example`. Swap them for real keys when you care about that locally.

### Frontend

```bash
cd client
cp .env.example .env
# API_URL should point at the backend, e.g. http://127.0.0.1:8000/api/v1
pnpm install
pnpm dev
```

App: `http://localhost:3000`

Sign in with the superuser you created. As staff you’ll see **Invites** - create a link, share it, someone registers with it.

---



## Self-hosting

This repo’s production path is AWS-shaped: Terraform for the API, Amplify for the UI, Cloudflare in front if you want DNS / Turnstile / rate limits. You can run the same apps elsewhere; the pieces just need to talk over HTTPS.

### Backend (AWS)

1. Copy `server/infra/terraform.tfvars.example` → `terraform.tfvars` and fill in real values (region, domains, DB URL, Django secret, Turnstile **secret** key, etc.).
2. Bootstrap and apply:

```bash
cd server/infra
./deploy.sh
```

1. Build and push the Lambda image, migrate, point Lambda at it:

```bash
cd server
./build.sh
```

SSM holds secrets Terraform writes (Django key, database URL, Turnstile secret). Lambda picks them up as env vars.

Point a Cloudflare CNAME at the API custom domain Terraform prints (`api_domain_target`). Keep that DNS **proxied** if you want WAF / rate limits on `/api/v1/auth/`*.

### Frontend (Amplify)

Connect the monorepo, set `appRoot` to `client` (see root `amplify.yml`), and set at least:

- `API_URL` — your public API base including `/api/v1`
- `NEXT_PUBLIC_TURNSTILE_SITE_KEY` — Turnstile **site** key for the production hostname

Attach your domain in Amplify. Use a Turnstile widget registered for that hostname (don’t reuse the localhost widget).

### After it’s up

1. Log in as admin.
2. Open **Invites**, create a link (email-locked or open).
3. Send the URL yourself - nothing emails on your behalf.
4. Invitee opens `/register?token=…`, completes Turnstile, and they’re in.

---



## Useful bits


| Command                     | Where           | What                     |
| --------------------------- | --------------- | ------------------------ |
| `make run` / `make migrate` | `server/`       | Local API                |
| `pnpm dev`                  | `client/`       | Local UI                 |
| `./deploy.sh`               | `server/infra/` | Terraform apply          |
| `./build.sh`                | `server/`       | Image → ECR → Lambda     |
| `./setup-admin.sh`          | `server/`       | First staff user in prod |


API health: `GET /api/v1/health`

If something auth-related fails in prod, check Turnstile keys match (site on Amplify, secret on Lambda), and that the invite wasn’t revoked or expired.