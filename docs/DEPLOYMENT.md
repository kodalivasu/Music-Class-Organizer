# Music Class Organizer — Deployment Guide

This doc covers how to deploy the app so teachers, students, and parents can access it over the internet. **HTTPS is required** for production.

---

## 1. HTTPS requirement

**You must serve the app over HTTPS in production.**

| Reason | Why it matters |
|--------|----------------|
| **Session cookies** | Auth uses a signed cookie (`SESSION_SECRET`). Over HTTP, cookies can be intercepted; browsers may not treat them as secure. |
| **Login flows** | Teacher password, student PIN, and parent magic-link logins must not be sent in the clear. |
| **Best practice** | Modern browsers and app stores expect HTTPS; some features (e.g. secure cookies, MediaRecorder in some contexts) behave correctly only over HTTPS. |

The app itself runs as an **HTTP** server (Python’s `HTTPServer`). TLS/HTTPS is provided by:

- **PaaS:** The platform (e.g. Railway, Render) terminates HTTPS and forwards HTTP to your app.
- **Reverse proxy:** You run the app behind Caddy, nginx, or similar; the proxy terminates HTTPS and proxies to `localhost:8000` (or your chosen port).

Do **not** expose the built-in Python server directly to the internet on HTTP.

---

## 2. Pre-deploy checklist

Use this before going live.

### Environment variables

| Variable | Required in prod? | Notes |
|----------|-------------------|--------|
| `SESSION_SECRET` | **Yes** | Long random string; e.g. `openssl rand -hex 32`. The app refuses to bind to non-localhost if you still use the dev default. On Render, the app will start anyway (with a warning) so the service can come up; set `SESSION_SECRET` in Render Environment for production security. |
| `HOST` | Optional | Set to `0.0.0.0` if the process must accept external connections (e.g. behind a reverse proxy). |
| `PORT` | Optional | Default `8000`. PaaS often sets this automatically. |
| `GOOGLE_API_KEY` | Optional | Needed for AI features (explain raga, find recordings). App runs without it; AI features disabled. |

- [ ] `SESSION_SECRET` set to a strong random value (not `dev-secret-change-in-production`).
- [ ] `.env` (or platform env config) is not committed; only `.env.example` is in repo.

### Data and media

- [ ] `data/` is present and populated (e.g. `audio_categories.json`, `events.json`, tenant/DB if used).
- [ ] `media/` is present if you serve audio/video/photos from disk (or configured for your storage).
- [ ] If using SQLite (`db/` or path from app), the DB file is on a persistent volume where the platform supports it.

### Run command

- [ ] App starts with: `python src/app.py` (from project root so `data/` and `media/` resolve).
- [ ] Working directory is the project root (where `data/`, `media/`, `src/` live).

### Post-deploy smoke test

- [ ] Homepage loads over **HTTPS**.
- [ ] Teacher login works (password).
- [ ] Student login works (PIN) and parent magic link works if used.
- [ ] Music library and events load; audio plays (range requests work for iOS Safari when applicable).

---

## 3. PaaS options (HTTPS included)

These platforms provide TLS and usually a public URL. You run the app as an HTTP service; they handle HTTPS.

| Platform | HTTPS | Notes |
|----------|--------|--------|
| **Railway** | Yes (automatic) | Add repo, set env vars, set start command `python src/app.py`. Persistent volume for `data/`/`media/` if needed. |
| **Render** | Yes (automatic) | Web Service, build: none (or minimal), start: `python src/app.py`. Add disk for persistence. |
| **Fly.io** | Yes (automatic) | Docker or `fly launch` with a Procfile/start command. Mount volumes for `data/` and `media/`. |
| **PythonAnywhere** | Yes (automatic) | WSGI or “run a script”; may need to adapt to their process model. Good for small teams. |
| **Heroku** | Yes (automatic) | Add Procfile: `web: python src/app.py` (or use a production WSGI server if you add one). |

**Typical steps (generic):**

1. Connect repo to the PaaS.
2. Set env: `SESSION_SECRET`, optionally `HOST=0.0.0.0`, `PORT` if fixed, `GOOGLE_API_KEY` if using AI.
3. Set start command: `python src/app.py`; ensure run from project root.
4. If the app writes to `data/` or `media/`, attach a persistent volume/disk and point paths there (or use object storage later).
5. Open the generated **HTTPS** URL and run the smoke tests above.

---

## 4. Reverse-proxy options (VPS / self-hosted)

If you run the app on a VPS (e.g. Linux VM), run it bound to `127.0.0.1:8000` and put a reverse proxy in front that terminates HTTPS.

### Caddy (recommended: automatic HTTPS)

- Gets a certificate automatically (e.g. Let’s Encrypt) for your domain.
- Minimal config:

```text
your-domain.com {
    reverse_proxy localhost:8000
}
```

- [ ] Install Caddy, set `your-domain.com` and DNS, start Caddy.
- [ ] Run app: `HOST=127.0.0.1 PORT=8000 python src/app.py` (or with `systemd`/supervisor).

### Nginx

- Use a TLS config (e.g. with `ssl_certificate` from Let’s Encrypt/certbot).
- Proxy to `http://127.0.0.1:8000` for the app.
- [ ] Certbot (or similar) for certificates.
- [ ] Nginx proxy pass to `localhost:8000`; run app on `127.0.0.1:8000`.

### Cloudflare Tunnel (no open inbound ports)

- Run `cloudflared tunnel` on the same machine as the app; Cloudflare handles HTTPS and DDoS protection.
- [ ] Create tunnel, point to `http://localhost:8000`; use a Cloudflare-managed hostname (HTTPS by default).

### Summary

| Option | HTTPS | Best for |
|--------|--------|----------|
| **Caddy** | Auto (Let’s Encrypt) | Simple reverse proxy with minimal config. |
| **Nginx** | With certbot/ACME | Existing nginx setups. |
| **Cloudflare Tunnel** | Via Cloudflare | No port 80/443 open on your machine. |

---

## 5. Quick reference

- **HTTPS:** Required; use PaaS TLS or a reverse proxy. Do not expose the app’s HTTP server directly.
- **Checklist:** Strong `SESSION_SECRET`, correct env, `data/`/`media/` (or persistent storage), run from project root, smoke test over HTTPS.
- **PaaS:** Railway, Render, Fly.io, PythonAnywhere, Heroku — set env and start command, add persistence if needed.
- **Self-hosted:** Caddy (easiest), nginx + certbot, or Cloudflare Tunnel; app on `127.0.0.1:8000`.

After deployment, update `docs/requirements.md` and `docs/PRD.md` if you add new env vars or deployment paths.
