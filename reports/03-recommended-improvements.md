# 03 – Recommended Improvements

Fixes are ordered by value for effort. The code is in [`../code-snippets`](../code-snippets/) and is written in **Python (FastAPI + Pydantic)**.

> **Note on the stack.** Cynbit's site is a Next.js application (inferred, see the audit report), so these exact files would not be dropped into it. They show the same controls in Python, which I can write and test; each control has a direct equivalent in Next.js (Server Action validation, `next.config.js` headers, middleware rate limiting, background work after the response). The snippets were tested locally with FastAPI's test client; the DNS e-mail check was **not** exercised because it needs internet DNS.

## Priority 1 – Quick wins (about a day)

### 1. Validate every form on the server → F-01, F-02, F-03
Anything a browser can send, a script can send too, so validation must live on the server for every form. Use a schema with:
* trimmed strings with minimum and **maximum lengths**
* unknown fields rejected
* e-mail syntax check **plus a DNS (MX/A record) check**
* Indian mobile format, plausible date of birth, and `agreed_to_terms` required

Important nuance: a syntax or regex check **still accepts** `name@gmail.commmm` (my test confirms it passes syntax). Only a DNS check or a confirmation e-mail (double opt-in) catches it, so add the confirmation step for the newsletter.
→ [`input-validation.py`](../code-snippets/input-validation.py)

### 2. Add security headers → F-05, F-06, F-08
Set `Content-Security-Policy` (start as *Report-Only*), `X-Frame-Options`/`frame-ancestors`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, extend HSTS, and replace wildcard CORS with an explicit origin list.
→ [`security-headers.py`](../code-snippets/security-headers.py)

### 3. Stop abuse → F-04
* Honeypot field (zero cost)
* Rate limit per IP (e.g. 3 newsletter signups / 10 min, 5 contact messages / 10 min); returns HTTP 429. Key limits by endpoint/action, since Cynbit's newsletter and contact share one URL.
* Cloudflare Turnstile token verified server-side
→ [`rate-limiting.py`](../code-snippets/rate-limiting.py)

## Priority 2 – Backend quality (a few days)

### 4. Respond fast, work later → F-10
Validate, write one indexed row, return. Send the notification e-mail and CRM sync after the response (FastAPI `BackgroundTasks`, or a real queue such as Celery/RQ/arq so failures retry). Keep the database in the same region as the application server.
→ [`caching-compression.py`](../code-snippets/caching-compression.py)

### 5. Idempotent writes and consistent errors → F-02
Unique constraint on e-mail so duplicates are handled by the database; one error envelope with real HTTP status codes (422 validation, 429 rate limit, 500 server) so monitoring can count failures; no submitted data echoed back; generic user messages, details only in logs; same response for "new" and "already subscribed" to prevent e-mail enumeration.
→ [`error-handling.py`](../code-snippets/error-handling.py)

### 6. Reduce collected personal data → F-03
Collect date of birth, mobile and WhatsApp only if recruiting needs them; add a consent line and a retention period; verify the e-mail (confirmation link) and, if it matters, the mobile (OTP).

## Priority 3 – Performance and hygiene

### 7. Compression and caching → F-11
Brotli with gzip fallback, immutable caching for fingerprinted static assets, ETag + short `max-age` for public GET data (repeat visits get `304`), `no-store` for writes. → [`caching-compression.py`](../code-snippets/caching-compression.py)
Front-end side: analyze the JavaScript bundle, lazy-load below-the-fold components, defer analytics until consent, render one navigation tree instead of two (F-12). Re-run Lighthouse; aim for mobile ≥ 90.

### 8. Canonical host, sitemap, robots → F-07, F-15
One host (`www`) in redirects, sitemap and certificate; real `lastmod` dates; make sure `/admin`, `/portal`, `/api` require authentication and return 401/403 (do not rely on `robots.txt`).

### 9. Privacy and cookies → F-09, F-14
Gate analytics behind consent (Google Consent Mode v2), update the cookie policy to match the cookies actually set, and use `HttpOnly; Secure; SameSite=Lax` for any future session cookie.

### 10. Fix the broken asset → F-13
Correct the image path and add an automated check for 404 assets (CI link check or uptime monitor).

## How to verify the fixes

| Fix | Check |
|-----|-------|
| Validation | `a@gmail.commmm` → rejected (with DNS check on); 10 000-character message → 422 |
| Headers | `curl -I https://www.cynbit.in` shows the new headers; securityheaders.com grade A |
| Rate limit | 4th newsletter request in 10 min → HTTP 429 |
| Async | Form POST time drops well under 1 s in DevTools |
| Lighthouse | Mobile Performance ≥ 90, unused JS reduced |

## Running the snippets

```bash
pip install fastapi uvicorn pydantic email-validator slowapi httpx brotli-asgi
# file names contain hyphens for readability; copy a snippet to e.g. app.py (or rename with underscores)
uvicorn app:app --reload --no-server-header
```
