# Evidence index

Four images hold all the evidence. Each is a vertical stack of DevTools/browser screenshots; every panel has a blue banner with its figure number (**Fig. NN**) and a caption, and the reports cite those numbers.

Captured with Firefox and Chrome DevTools on 31 Oct – 1 Nov 2026, as a normal visitor. Form data is deliberately fake test data. Cookie values visible in some panels are analytics client IDs from my own browser session.

## network-tab.png
Form requests, responses, timings and caching behaviour.

| Fig. | What it shows | Used in |
|------|---------------|---------|
| 03 | Contact form request payload (multipart fields `_1_fullName`, `_1_email`, `_1_company`, `_1_industry`, `_1_message`) | Audit §3 |
| 06 | AI services inquiry payload (`fullName`, `email`, `techStack`, `goal`, `message`, `agreedToTerms`, `serviceType`) | Audit §3 |
| 09 | Demo form accepted `jnejneen@gmail.commmm` | F-01 |
| 12 | Contact form accepted `alpjfdd@njkkssl.com` | F-01 |
| 14 | Newsletter success screen and response `{"success":true,"message":"Success! Welcome to the network."}` | Audit §3 |
| 16 | Contact POST timings (about 1.45 s and 3.0 s) and repeated analytics calls | F-10, F-14 |
| 17 | POST `/contact` response and request headers (`no-store`, `server: Vercel`, `next-action`) | Audit §3–4 |
| 18 | Newsletter payload accepted `krijfjfffjf@gmail.ccccncn`; no token or CAPTCHA field | F-01, F-04 |
| 19 | Newsletter POST headers (`text/plain`, its own `next-action` ID) and analytics calls | Audit §3, F-14 |
| 22 | Career application POST to `/careers/[slug]` (about 3.1 kB body) | F-03 |
| 29 | RSC prefetch with `If-None-Match` / `304` caching | Audit §4 |

## response-headers.png
Headers, transport security, public files and error page.

| Fig. | What it shows | Used in |
|------|---------------|---------|
| 26 | `GET /` document headers: HSTS present; no CSP, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` or `Permissions-Policy`; `access-control-allow-origin: *`; `x-vercel-cache: HIT`; Brotli | F-05, F-06, F-08, Audit §2, §4 |
| 08 | POST `/products` response headers (HSTS, `no-store`, `server: Vercel`) | F-08, Audit §4 |
| 05 | Firefox Security panel: TLS 1.3, Let's Encrypt certificate, validity dates (HSTS shows "Disabled" only because Firefox had not cached the policy; the header itself is present in Fig. 26) | Audit §2, F-08 |
| 13 | Certificate details: Subject Alt Name lists only `www.cynbit.in` | F-15, Audit §2 |
| 24 | `robots.txt` with `Disallow: /api/`, `/admin/`, `/portal/` (paths not visited) | F-07 |
| 25 | Branded 404 page with no stack trace or framework details | Positives |

## lighthouse-report.png
Front-end performance, accessibility and rendering observations.

| Fig. | What it shows | Used in |
|------|---------------|---------|
| 20 | Lighthouse mobile insights: render-blocking 710 ms, 611 KiB unused JS, 6.2 s main-thread work, 2.1 s JS execution, 13 long tasks | F-11 |
| 15 | Lighthouse mobile scores (Performance 76, Accessibility 86, Best Practices 96, SEO 100) and accessibility issues | F-11 |
| 11 | Case-study hero image fails to load (alt text only) | F-13 |
| 27, 28 | Raw HTML preview showing the navigation markup twice (desktop and mobile). The unstyled look is only the Response preview without CSS | F-12 |

## cookies-or-auth.png
Cookies, browser storage and the cookie policy.

| Fig. | What it shows | Used in |
|------|---------------|---------|
| 01 | Only Google Analytics cookies (`_ga`, `_ga_LK6CQWCWX0`, `_gcl_au`); no session or auth cookie | F-09, F-14 |
| 10 | Local storage keys `cynbit_newsletter_seen` and `_gcl_ls`; no personal data | F-09 |
| 02 | Cookie policy text about "essential cookies" that were not observed | F-09 |

## Not captured as images
These points come from my testing notes or from text files, so they are labelled *reported* in the findings:

* F-02 (no length limits or duplicate handling) and F-03 (career-form fields with no verification): notes only; Fig. 22 shows the request but not its fields.
* F-04: the payloads (Figs. 03, 06, 18) show no token or CAPTCHA field; the absence of rate limiting is from notes, and thresholds were not load-tested.
* `sitemap.xml`: text captured; an excerpt is in the audit report §6.