# 02 – Security & Performance Findings

Severity scale: **High** = direct exposure of users/data · **Medium** = weakens defenses or causes real operational cost · **Low** = best-practice gap · **Info** = observation.
"Evidence" gives the figure number (printed on the banners inside the four images in `../evidence/`: `network-tab.png`, `response-headers.png`, `lighthouse-report.png`, `cookies-or-auth.png`) or says the point comes from my testing notes (*reported*).
Fix details and code: [03-recommended-improvements.md](03-recommended-improvements.md).

---

## A. Data validation

### F-01 – Unreal e-mail addresses are accepted (Medium)
* **Observation:** The newsletter accepted `krijfjfffjf@gmail.ccccncn`; the demo form accepted `jnejneen@gmail.commmm`; the contact form accepted `alpjfdd@njkkssl.com`. No client-side message appeared and the server returned success.
* **Evidence:** Fig. 18, 09, 12 (confirmed).
* **Impact:** Junk and bounced addresses pollute the mailing list and CRM, hurt sender reputation, and let anyone sign up someone else's address (no ownership check). The "25k+ subscribers" figure on the site cannot be trusted if the list is unverified.
* **Fix:** Server-side schema validation, MX lookup, and (the real fix) double opt-in confirmation e-mail. Note that a plain regex still accepts `gmail.commmm`; only an MX check or confirmation e-mail catches it.

### F-02 – No input length limits or duplicate handling observed (Low–Medium)
* **Observation:** No `maxlength`/limit messages in forms; repeated identical submissions were accepted without any "already subscribed/received" response.
* **Evidence:** Tester notes (*reported*). Server-side limits are *unverified*.
* **Impact:** Oversized payloads, storage bloat, duplicate rows and duplicate notification e-mails.
* **Fix:** Max lengths in the schema, unique constraint on e-mail, idempotent upsert.

### F-03 – Career forms collect sensitive personal data with no verification (Medium)
* **Observation:** The internship/career forms collect e-mail, date of birth, mobile number and WhatsApp number; none are format-checked or verified.
* **Evidence:** Tester notes (*reported*); POST seen in Fig. 22 (`/careers/[slug]`, ~3.1 kB body).
* **Impact:** Bad data for recruiters and a larger privacy obligation (DOB + phone) without a matching consent/retention statement visible in the form.
* **Fix:** Field-level validation (E.164/Indian mobile format, plausible DOB range, e-mail verification), collect only what is needed, and show a consent/retention note.

## B. Security

### F-04 – No anti-automation control observed (Medium)
* **Observation:** No CAPTCHA token, honeypot field or rate-limit response in any form payload; repeated submissions were accepted in testing.
* **Evidence:** Payloads in Figs. 03, 06, 09, 18 contain only user fields; notes (*reported*). Thresholds were **not** load-tested (out of scope), so a limit may exist at the platform level.
* **Impact:** Spam floods the inbox/CRM and can run up e-mail/DB costs.
* **Fix:** Per-IP and per-e-mail rate limit, Cloudflare Turnstile (or reCAPTCHA), honeypot field.

### F-05 – Key browser security headers are not set (Medium)
* **Observation:** The `GET /` response contains HSTS but **no** `content-security-policy`, `x-frame-options` (or CSP `frame-ancestors`), `x-content-type-options`, `referrer-policy` or `permissions-policy`.
* **Evidence:** Fig. 26 (confirmed on the document response).
* **Impact:** Pages (including forms) can be framed by other sites (clickjacking); no CSP means no second line of defense against XSS; MIME sniffing is not disabled.
* **Fix:** Add the headers in one place (middleware or reverse proxy); start CSP in report-only mode because of Google Analytics. See `code-snippets/security-headers.py`.

### F-06 – Wildcard CORS on the HTML document (Low)
* **Observation:** `access-control-allow-origin: *` on `GET /`.
* **Evidence:** Fig. 26.
* **Impact:** Low for a public page, but it must not apply to routes that return user-specific data. This looks like a platform default; verify it does not also appear on future API routes.
* **Fix:** Restrict CORS to required routes/origins.

### F-07 – `robots.txt` reveals sensitive route names (Low)
* **Observation:** Disallow entries for `/api/`, `/admin/`, `/portal/`.
* **Evidence:** Fig. 24. These paths were **not** visited.
* **Impact:** Tells an attacker where privileged areas are; `robots.txt` is advice to crawlers, not access control.
* **Fix:** Ensure those routes require authentication and return 401/403; use `noindex` headers or auth instead of listing them (or accept the disclosure knowingly).

### F-08 – HSTS lacks `includeSubDomains` / `preload` (Low)
* **Observation:** `strict-transport-security: max-age=63072000` only. (Firefox's Security panel showed "Disabled" for the host because it had not cached the policy; the header itself is present.)
* **Evidence:** Fig. 08, 26, 05.
* **Fix:** `max-age=63072000; includeSubDomains; preload` once all subdomains are HTTPS-only.

## C. Authentication and privacy

### F-09 – No auth surface visible; cookie policy does not match observed cookies (Info)
* **Observation:** No login or session cookie on the public site; only GA cookies and two local-storage keys. The cookie policy says disabling "essential cookies" may break inquiry forms, but the forms need no cookie. `/portal/` and `/admin/` exist per `robots.txt` but were not tested.
* **Evidence:** Fig. 01, 02, 10.
* **Impact:** Authentication could not be assessed. The policy text is slightly inaccurate.
* **Fix:** When auth is used, set session cookies `HttpOnly; Secure; SameSite=Lax`; align the cookie policy with reality.

### F-14 – Analytics fires on every interaction; consent behaviour unverified (Info)
* **Observation:** Repeated `collect?v=2&tid=G-…` requests; GA cookies are present.
* **Evidence:** Fig. 16, 19, 01. I did not observe a consent banner or Consent Mode state.
* **Fix:** Load analytics only after consent (Google Consent Mode v2) where required.

## D. Performance

### F-10 – Slow form responses (Medium)
* **Observation:** Contact POSTs took ≈ 1.45 s and ≈ 3.0 s; the newsletter took ≈ 2.67 s for the DB step and ≈ 4.25 s end-to-end (tester-measured).
* **Evidence:** Fig. 16 (confirmed), notes (*reported*).
* **Impact:** Users wait several seconds and may double-submit (which, combined with F-02, creates duplicates). Slow work is probably in the request path (DB + e-mail).
* **Fix:** Validate → write → respond; do notifications after the response (background task or queue); keep DB and functions in the same region.

### F-11 – Heavy JavaScript on mobile (Low–Medium)
* **Observation:** Lighthouse mobile: Performance 76, Accessibility 86, Best Practices 96, SEO 100. Insights: ~611 KiB unused JavaScript, 6.2 s main-thread work, 2.1 s JS execution, 710 ms render-blocking requests, 13 long tasks, ~81 KiB minification savings, ~11 KiB legacy JS. Accessibility: list semantics, touch-target size, heading order.
* **Evidence:** Fig. 15, 20.
* **Fix:** Code-split heavy client components, lazy-load below-the-fold sections and third-party scripts, analyze the bundle, fix a11y issues.

### F-12 – Duplicate navigation markup (Info)
* **Observation:** The raw HTML contains the navigation (Company / Expertise / BitElevate groups) twice – once for the desktop menu and once for the mobile menu.
* **Evidence:** Fig. 27, 28. (The unstyled look is just the Response preview without CSS.)
* **Fix:** Render one navigation and restyle responsively, or render the mobile menu only when opened.

## E. Reliability and consistency

### F-13 – Broken image on a case-study page (Low)
* **Observation:** The hero image shows only alt text and an empty container.
* **Evidence:** Fig. 11.
* **Fix:** Fix the asset path, use `next/image` with a fallback, add monitoring for 404 assets.

### F-15 – Host and sitemap inconsistencies (Low)
* **Observation:** Sitemap URLs use `https://cynbit.in/...` while the site serves `https://www.cynbit.in`; every static `lastmod` equals the generation time; the certificate lists only `www.cynbit.in` as a name.
* **Evidence:** Fig. 13 and the sitemap file.
* **Impact:** Crawlers follow an extra redirect and may split signals; `lastmod` is not meaningful.
* **Fix:** One canonical host everywhere (sitemap, canonical tags, redirects), real `lastmod` values from content dates; confirm the apex certificate/redirect is valid.

---

## Positives (what is done well)

* TLS 1.3, valid certificate, HSTS with 2-year max-age (Fig. 05, 26)
* HTTP/2, Brotli, edge caching with ETag/304 (26, 29)
* `no-store` on server-action responses (08, 17)
* Branded 404 without leakage (25)
* No unnecessary server/version disclosure beyond `server: Vercel`
* Lighthouse SEO 100 and Best Practices 96 (15)
