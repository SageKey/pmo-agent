# Deploying the React + FastAPI Stack

This guide walks you through shipping the full app to **Vercel** (frontend) and **Railway** (backend) so it's accessible from anywhere via a shared-password gate.

> **TL;DR**
> 1. Push the repo to GitHub `main`
> 2. Deploy the backend to Railway (connects to the repo, builds from `backend/Dockerfile`, mounts a persistent volume at `/data`)
> 3. Deploy the frontend to Vercel (root directory = `frontend/`)
> 4. Wire env vars on both sides
> 5. Share the URL + password with your friends

---

## 1. Prerequisites

- A GitHub repo with this code pushed to `main` (`SageKey/pmo-agent` in this project)
- A [Railway](https://railway.app) account (free trial, then ~$5/mo for the hobby plan + volume)
- A [Vercel](https://vercel.com) account (free hobby plan is plenty)
- Your `ANTHROPIC_API_KEY` — only needed if you want to enable the AI Assistant on the shared deploy. **Default is to leave it off** (`PUBLIC_MODE=true`) so friends can't burn your LLM credit.
- Your `JIRA_API_TOKEN` — only needed if you want the "Sync Jira" button to actually sync on the shared instance

---

## 2. Backend → Railway

### 2a. Create the service

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → pick your `pmo-agent` repo
2. Railway will detect the `backend/Dockerfile` automatically. If it asks for a root directory, leave it at repo root (the Dockerfile copies engine files from there).
3. Wait for the first build to finish (~3-5 min — ortools is a chunky wheel)

### 2b. Add a persistent volume

SQLite files live on disk, so you **must** mount a volume or your data resets every redeploy.

1. In the service settings → **Volumes** → **New Volume**
2. **Mount path:** `/data`
3. **Size:** 1 GB is plenty
4. Redeploy

The `Dockerfile` already sets `DB_PATH=/data/pmo_data.db` and `SNAPSHOT_DB_PATH=/data/pmo_snapshots.db`, so the DB will be created on the volume on first boot. The startup hook seeds it from `seed_data.sql` automatically.

### 2c. Set environment variables

Service → **Variables** → add:

| Variable | Value | Purpose |
|---|---|---|
| `SHARED_PASSWORD` | *a memorable passphrase* | Required. Without this, the API is wide open. |
| `PUBLIC_MODE` | `true` | Hides AI Assistant + disables `/agent/*` routes. **Leave this on** unless you want friends burning LLM credit. |
| `CORS_ORIGIN_PROD` | `https://your-vercel-url.vercel.app` | Once Vercel is deployed, add this so the browser can call the backend. Comma-separated if you want multiple origins. |
| `ANTHROPIC_API_KEY` | *optional* | Only if `PUBLIC_MODE=false` and you want the agent enabled |
| `JIRA_API_TOKEN` | *optional* | `email:token` format, enables the Sync Jira button |

### 2d. Grab the public URL

Service → **Settings** → **Networking** → **Generate Domain** → you'll get something like `pmo-agent-backend-production.up.railway.app`. Save this — the frontend needs it.

### 2e. Verify

```bash
curl https://YOUR-BACKEND.up.railway.app/api/v1/meta/health
```

Should return JSON with `auth_required: true, public_mode: true`. No X-Share-Key header needed for this endpoint — it's on the allowlist so the frontend can bootstrap.

```bash
curl -H "X-Share-Key: YOUR_PASSWORD" https://YOUR-BACKEND.up.railway.app/api/v1/portfolio/
```

Should return the project list.

---

## 3. Frontend → Vercel

### 3a. Create the project

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project** → import your GitHub repo
2. **Root Directory:** set to `frontend/` (important — this is a monorepo)
3. Framework preset should auto-detect as **Vite**
4. Leave build/output settings at defaults (they match `vercel.json`)

### 3b. Set environment variables

Before the first deploy, set:

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://YOUR-BACKEND.up.railway.app/api/v1` |

Vercel will inject this at build time.

### 3c. Deploy

Click **Deploy**. You'll get a `https://pmo-agent.vercel.app` URL (or similar) in ~1 minute.

### 3d. Loop back to Railway

Go back to your Railway service's env vars and set:

```
CORS_ORIGIN_PROD=https://your-actual-vercel-url.vercel.app
```

Railway will redeploy automatically.

### 3e. Verify the end-to-end

1. Open your Vercel URL in a browser
2. You should see the password modal
3. Enter your `SHARED_PASSWORD`
4. Every page should load with real data
5. The sidebar should NOT show "AI Assistant" (because `PUBLIC_MODE=true`)
6. Try editing a project to confirm writes work

---

## 4. Sharing with friends

Just send them:

- The Vercel URL
- The password

Their browser will remember the password in `localStorage` after the first entry. They can use the app normally.

### What friends can do
- View every page with real data
- Edit project details, add/remove milestones, log timesheets, etc.
- Run Jira sync (if you configured `JIRA_API_TOKEN`)

### What friends can't do
- Access the AI Assistant (hidden by `PUBLIC_MODE`)
- Call `/agent/*` endpoints (the router is never mounted when `PUBLIC_MODE=true`)
- Bypass the password (every route except `/meta/health` checks the header)

### Rotating the password

1. Railway → your service → Variables → update `SHARED_PASSWORD`
2. Railway will redeploy (~30s)
3. Everyone's current session breaks with a 401. The frontend auto-detects this, clears the cached key, and shows the login modal again.
4. Text the new password out.

---

## 5. Enabling the AI Assistant later

When you want to demo the agent to a specific friend:

1. Railway → Variables → set `PUBLIC_MODE=false`
2. Set `ANTHROPIC_API_KEY=sk-ant-...`
3. Railway redeploys
4. The sidebar shows "AI Assistant" again and the chat works
5. **Remember to flip it back off when the demo is done** — each message costs ~$0.10-0.20 and anyone with the password can spam it

A future improvement would be per-user rate limiting or a separate "dev token" gate on top of `PUBLIC_MODE`, but for now the flip-on / flip-off workflow is simplest.

---

## 6. Local dev unchanged

None of this affects local development. Running the app locally:

```bash
# Terminal 1 — backend
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

...still works exactly as before. The auth middleware only activates when `SHARED_PASSWORD` is set, and `PUBLIC_MODE` defaults to `false`. Your local `backend/.env` keeps both keys available for the agent + Jira sync.

---

## Troubleshooting

**Backend 500s on first boot**
Check Railway logs for seed errors. The startup hook tries to run `seed_data.sql` against an empty volume. If the seed file has schema bugs, fix it locally and redeploy.

**Frontend shows "Network Error"**
Either `VITE_API_BASE_URL` isn't set correctly, or `CORS_ORIGIN_PROD` on Railway doesn't match the Vercel domain. Check both.

**401 on every request after a redeploy**
Expected — old share keys in localStorage don't match the new `SHARED_PASSWORD`. The frontend auto-clears and re-prompts.

**Railway volume fills up**
SQLite + the snapshot store should stay well under 100 MB for the foreseeable future. If it somehow fills, bump the volume size in Railway settings.

**AI Assistant missing when I want it**
Make sure `PUBLIC_MODE=false` AND `ANTHROPIC_API_KEY` is set. If the sidebar still hides it, open DevTools → Application → Local Storage → clear `pmo.share_key` and reload to force a fresh `/meta/health` fetch.
