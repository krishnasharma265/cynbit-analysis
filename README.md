# Cynbit – Analysis From a Backend Perspective

**Task:** Backend Developer Intern – Technical Assessment
**Author:** Krishna Sharma
**Target:** https://www.cynbit.in (public website only)
**Analysis window:** 31 Oct – 1 Nov 2026

## Scope and ethics

Everything here comes from **passive, authorized observation**: browsing the public site like a normal visitor, reading browser DevTools (Network, Application, Security, Lighthouse), reading public files (`robots.txt`, `sitemap.xml`), and submitting the public forms a small number of times with clearly fake test data.

I did **not** exploit, fuzz, overload, brute-force, or probe any endpoint. The paths listed in `robots.txt` (`/api/`, `/admin/`, `/portal/`) were deliberately **not** visited. Anything that cannot be seen from outside is marked *unverified* rather than guessed. Test submissions were made with fake data and the team may want to delete them from their inbox/database.

## What I found (summary)

The site is a Next.js (App Router) application on Vercel. Transport security and hosting are solid. The weaknesses are mostly on the **form/backend side**: weak input validation, no visible abuse protection, slow form responses, and missing browser security headers.

| ID | Category | Finding | Severity | Evidence |
|----|----------|---------|----------|----------|
| F-01 | Data validation | Malformed/unreal emails accepted (`@gmail.commmm`, `@gmail.ccccncn`) by newsletter, contact and demo forms | Medium | Fig. 09, 12, 18 |
| F-02 | Data validation | No input length limits or duplicate handling observed | Low–Medium | Tester notes (reported) |
| F-03 | Data validation | Career forms collect email, DOB, mobile, WhatsApp with no verification | Medium | Tester notes (reported), Fig. 22 |
| F-04 | Security | No anti-automation control (CAPTCHA/token/rate limit) observed on any form | Medium | Payloads 03, 06, 18; notes |
| F-05 | Security | CSP, X-Frame-Options/frame-ancestors, X-Content-Type-Options, Referrer-Policy, Permissions-Policy not set on the document response | Medium | Fig. 26 |
| F-06 | Security | `access-control-allow-origin: *` on the HTML document | Low | Fig. 26 |
| F-07 | Security | `robots.txt` discloses `/api/`, `/admin/`, `/portal/` | Low | Fig. 24 |
| F-08 | Security | HSTS present but without `includeSubDomains` / `preload` | Low | Fig. 08, 26 |
| F-09 | Authentication / privacy | No auth surface visible; only analytics cookies; cookie policy mentions "essential cookies" that were not observed; consent mechanism not observed | Info | Fig. 01, 02, 10 |
| F-10 | Performance (backend) | Form submissions take ~1.5–3 s; newsletter ~4.25 s end-to-end (measured) | Medium | Fig. 16; notes |
| F-11 | Performance (frontend) | Lighthouse mobile Performance 76: 611 KiB unused JS, 6.2 s main-thread work, 710 ms render-blocking | Low–Medium | Fig. 15, 20 |
| F-12 | Performance | Navigation markup appears twice in the HTML (desktop + mobile) | Info | Fig. 27, 28 |
| F-13 | Reliability | Case-study hero image fails to load | Low | Fig. 11 |
| F-14 | Privacy | Analytics fires on every interaction; consent behaviour should be verified | Info | Fig. 16, 19 |
| F-15 | Consistency | Sitemap uses apex host while site serves `www`; sitemap `lastmod` is generation time; certificate names only `www` | Low | Fig. 13, sitemap |

**Positives:** TLS 1.3 with valid Let's Encrypt certificate, HSTS with 2-year max-age, HTTP→HTTPS and canonical-host redirects, HTTP/2 + Brotli, edge caching with ETag/304, `no-store` on form responses, branded 404 page with no information leakage, no server version disclosure beyond `server: Vercel`.

## Reports

1. [Backend Technical Audit Report](reports/01-backend-technical-audit.md) – architecture, endpoints, payloads, caching, tech stack
2. [Security & Performance Findings](reports/02-security-performance-findings.md) – categorized findings with evidence
3. [Recommended Improvements](reports/03-recommended-improvements.md) – prioritized fixes with code

## Code snippets (Python, FastAPI + Pydantic)

| File | Fixes | Purpose |
|------|-------|---------|
| [security-headers.py](code-snippets/security-headers.py) | F-05, F-06, F-08 | Security headers middleware, explicit CORS origins |
| [rate-limiting.py](code-snippets/rate-limiting.py) | F-04 | Per-IP rate limit (HTTP 429), honeypot, Cloudflare Turnstile |
| [input-validation.py](code-snippets/input-validation.py) | F-01, F-02, F-03 | Pydantic schemas, length limits, DNS e-mail check, mobile/DOB validation |
| [caching-compression.py](code-snippets/caching-compression.py) | F-10, F-11 | Brotli/gzip, cache headers + ETag/304, background tasks for slow work |
| [error-handling.py](code-snippets/error-handling.py) | F-02 | One error envelope, real status codes, safe messages, duplicate handling |

**Why Python?** Cynbit's site is Next.js (inferred), so these files are not drop-in. They demonstrate the same controls in Python; each has a direct Next.js equivalent. The snippets were tested locally with FastAPI's test client (21 checks pass). The DNS e-mail check was not exercised because it needs internet DNS. Hyphenated file names are for readability: copy a snippet to `app.py` (or rename with underscores) to run it.

```bash
pip install fastapi uvicorn pydantic email-validator slowapi httpx brotli-asgi
```

## Evidence

Four images in [evidence/](evidence/). Each panel has a banner with its figure number (Fig. NN), which the reports cite.

| File | Figures |
|------|---------|
| `network-tab.png` | Fig. 03, 06, 09, 12, 14, 16, 17, 18, 19, 22, 29 – form payloads, responses, timings, caching |
| `response-headers.png` | Fig. 26, 08, 05, 13, 24, 25 – response headers, TLS/certificate, robots.txt, 404 page |
| `lighthouse-report.png` | Fig. 20, 15, 11, 27, 28 – Lighthouse results, broken image, navigation markup |
| `cookies-or-auth.png` | Fig. 01, 10, 02 – cookies, local storage, cookie policy |

## Limitations

Only the public front door was observed. Database, validation logic, email pipeline, and any admin/portal systems cannot be assessed from outside. Rate limits and abuse thresholds were intentionally not tested because that would require load, which the assessment forbids.
