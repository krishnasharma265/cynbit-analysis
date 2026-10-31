# Evidence index

All screenshots were taken from a normal browser session (Firefox / Chrome DevTools) on 31 Oct – 1 Nov 2026.
Test data in forms is deliberately fake.

| File | What it shows | Used in |
|------|---------------|---------|
| 01-cookies-ga-only.png | Only Google Analytics cookies (`_ga`, `_ga_*`, `_gcl_au`) are set | F-09 |
| 02-cookie-policy-page.png | Cookie policy text about "essential cookies" | F-09 |
| 03-contact-form-payload.png | Contact form request payload (multipart, fields `_1_fullName`, `_1_email`, ...) | Audit §3 |
| 04-form-response-success.png | Server action response `{"success":true}` | Audit §3 |
| 05-tls-security-panel.png | TLS 1.3, Let's Encrypt cert, validity dates | Audit §2 |
| 06-services-inquiry-payload.png | AI services inquiry payload (fullName, email, techStack, goal, message, agreedToTerms, serviceType) | Audit §3 |
| 07-rsc-response-contact.png | RSC (React Server Components) flight response after submit | Audit §3 |
| 08-demo-form-post-headers.png | POST /products response headers (HSTS present, `server: Vercel`, `no-store`) | F-05, Audit §4 |
| 09-demo-payload-invalid-email-accepted.png | Demo form accepted `jnejneen@gmail.commmm` | F-01 |
| 10-local-storage.png | Local storage keys (`cynbit_newsletter_seen`, `_gcl_ls`) | F-09 |
| 11-broken-case-study-image.png | Case-study hero image fails to load (alt text only) | F-13 |
| 12-contact-payload-unverified-domain.png | Contact form accepted `alpjfdd@njkkssl.com` | F-01 |
| 13-certificate-details.png | Certificate SAN lists only `www.cynbit.in` | F-15 |
| 14-newsletter-success-response.png | Newsletter success UI + response message | Audit §3 |
| 15-lighthouse-accessibility.png | Lighthouse accessibility 86 and issues | F-11 |
| 16-contact-post-timings.png | Contact POST timings (~1451 ms, ~3003 ms) | F-10 |
| 17-contact-post-headers.png | POST /contact response and request headers | Audit §4 |
| 18-newsletter-payload-invalid-email-accepted.png | Newsletter accepted `krijfjfffjf@gmail.ccccncn` | F-01 |
| 19-newsletter-post-headers.png | Newsletter POST headers (`text/plain`, own `next-action` id) | Audit §3 |
| 20-lighthouse-performance.png | Lighthouse insights: render-blocking, unused JS, main-thread time | F-11 |
| 21-services-post-headers.png | POST /services headers | Audit §3 |
| 22-careers-post-headers.png | POST /careers/[slug] headers | F-03 |
| 23-contact-form-ui.png | Contact form UI with optional fields | F-01/F-02 |
| 24-robots-txt.png | robots.txt Disallow list | F-07 |
| 25-404-page.png | Branded 404 page | Positives |
| 26-document-response-headers.png | `GET /` response headers (no CSP / XFO / XCTO / Referrer-Policy / Permissions-Policy; `access-control-allow-origin: *`) | F-05, F-06 |
| 27-nav-markup-part1.png, 28-nav-markup-part2.png | Raw HTML preview: navigation markup rendered twice | F-12 |
| 29-rsc-prefetch-304-caching.png | RSC prefetch with ETag / 304 | Audit §4 |

Note: cookie values in some screenshots are analytics client IDs from my own browser session.
