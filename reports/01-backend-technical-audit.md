# 01 – Backend Technical Audit Report

Target: `https://www.cynbit.in` · Method: passive observation only (see README for scope).
Figure numbers (Fig. NN) are printed on the banners inside the four images in [`../evidence`](../evidence/): `network-tab.png`, `response-headers.png`, `lighthouse-report.png`, `cookies-or-auth.png`.

## 1. Summary

Cynbit's site is a server-rendered **Next.js App Router** application hosted on **Vercel**. Form submissions are handled by **Next.js Server Actions** (not a classic REST API), so there are no separate `/api/...` endpoints visible in the browser. Static and prerendered pages are served from Vercel's edge cache.

## 2. Infrastructure and transport

| Item | Observation | Evidence |
|------|-------------|----------|
| Hosting / CDN | `server: Vercel`, `x-vercel-id`, `x-vercel-cache: HIT` (document) | 26 |
| Protocol | HTTP/2 | 08, 26 |
| TLS | TLS 1.3, `TLS_AES_128_GCM_SHA256`, RSA-2048 certificate | 05, 13 |
| Certificate | Let's Encrypt (YR2), valid 25 Sep 2026 → 24 Dec 2026, SAN: `www.cynbit.in` | 05, 13 |
| HSTS | `strict-transport-security: max-age=63072000` | 08, 26 |
| Compression | `content-encoding: br` (Brotli); document 100.5 kB → 16 kB transferred | 26 |
| Redirects | `http://` → HTTPS and apex → `www` redirect (tester-confirmed) | notes |

## 3. API / endpoint behaviour

All writes are `POST` requests to the **page route itself**; the target function is selected by the `next-action` request header (an opaque action ID). Bodies use the React/Next form-action encoding (`_1_<field>` parts plus a `0: ["$K1"]` part).

| Feature | Route (POST) | Content-Type | Fields observed | Evidence |
|---------|--------------|--------------|-----------------|----------|
| Contact inquiry | `/contact` | `multipart/form-data` | `fullName`, `email`, `company`, `industry`, `message` | 03, 12, 17 |
| Newsletter | `/contact` (different action ID) | `text/plain` | single JSON array containing the email | 18, 19 |
| AI services inquiry | `/services` | `multipart/form-data` | `fullName`, `email`, `techStack`, `goal`, `message`, `agreedToTerms`, `serviceType` | 06 |
| Schedule a demo | `/products` | `multipart/form-data` | `fullName`, `email`, `company`, `message`, `serviceType` ("Product: Studio") | 08, 09 |
| Career application | `/careers/[slug]` | `multipart/form-data` | multiple personal fields (payload ≈ 3.1 kB) | 22 |

**Responses.** Responses are React Server Component "flight" streams, e.g. `0:{"a":"$@1","f":"","b":"<buildId>"}` followed by `1:{"success":true}`; the newsletter adds a human message (`"Success! Welcome to the network."`). All captured submissions returned **HTTP 200** (Fig. 14, 17). The failure path (e.g. the empty message the tester saw rejected) was not captured, so how errors are signalled is *unverified*. Header `x-action-revalidated` is present, so the actions trigger cache revalidation, which explains several follow-up `POST` refreshes (Fig. 16, 17).

**Anti-abuse in the request.** No CAPTCHA token, honeypot, or custom token is present in any payload. (Next.js Server Actions have built-in Origin/Host checking, which I did not test; the requests carry `Origin: https://www.cynbit.in`.)

## 4. Caching and performance behaviour

| Resource | Header evidence | Observation |
|----------|-----------------|-------------|
| HTML document | `cache-control: public, max-age=0, must-revalidate`, `etag`, `x-vercel-cache: HIT`, `age: 196958`, `x-nextjs-prerender: 1`, `x-nextjs-stale-time: 300` | Prerendered, edge-cached, revalidated with ETag |
| RSC prefetches | `If-None-Match` → `304` | Efficient; ~13 route prefetches fire from the home page (each 0.6–3.7 kB) |
| Server-action responses | `cache-control: no-store, max-age=0, must-revalidate` | Correct for POST |
| Home page load (cache disabled) | 16 requests, 166.73 kB / 45.24 kB transferred, DOMContentLoaded 480 ms | Healthy |
| Whole browsing session | 219 requests, 1.28 MB | Mostly prefetch + analytics |

Form POST timings: contact submissions ≈ **1.45 s** and **3.0 s** (Fig. 16). Tester-measured newsletter: ≈ 2.67 s database check, 4.25 s total. Lighthouse (mobile, Chrome): Performance 76, Accessibility 86, Best Practices 96, SEO 100 (Fig. 15, 20).

## 5. State, cookies and storage

* Cookies: only `_ga`, `_ga_LK6CQWCWX0`, `_gcl_au` on `.cynbit.in` (Google Analytics / Ads); **no session, auth or CSRF cookie** (Fig. 01).
* Local storage: `cynbit_newsletter_seen=true`, `_gcl_ls` (Fig. 10) – no personal data.
* No login surface was observed in the public pages reviewed.

## 6. Public files and error handling

* `robots.txt` allows crawling, sets `Crawl-delay: 1`, and disallows `/api/`, `/admin/`, `/portal/` (Fig. 24). These paths were not visited.
* `sitemap.xml` lists ~15 static pages and ~16 blog posts; static entries use the apex host `https://cynbit.in/...` and a `lastmod` equal to generation time (e.g. `2026-10-31T19:33:57Z`).
* Sitemap excerpt (captured from `sitemap.xml`; all static entries look like this):
  ```xml
  <url><loc>https://cynbit.in/story</loc><lastmod>2026-10-31T19:33:57.952Z</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>
  ```
* 404 page: branded, offers navigation back, no stack trace or framework details (Fig. 25).

## 7. Inferred stack (confidence)

| Component | Confidence | Basis |
|-----------|-----------|-------|
| Next.js App Router + React Server Components | High | `rsc: 1`, `next-action`, `x-nextjs-prerender`, `text/x-component`, `/_next/static/chunks/...` |
| Vercel hosting | High | `server: Vercel`, `x-vercel-*` headers |
| Google Analytics 4 / Google Ads tag | High | `collect?v=2&tid=G-...`, `_ga*`, `_gcl_au` |
| Database / ORM / email provider | **Unknown** | Not observable from the client (Prisma, Supabase etc. are possibilities only) |

## 8. Architectural observations

1. Using Server Actions keeps the surface small (no public REST API), but all validation must live inside the action, because the client can send any multipart body.
2. Newsletter and contact share one route path (`/contact`), differentiated only by action ID – fine, but it makes route-level monitoring and rate limiting harder (limits must key on action name, not path).
3. Successful submissions return HTTP 200 with a flight body; if failures also return 200 (unverified), uptime/error monitoring cannot rely on status codes.
