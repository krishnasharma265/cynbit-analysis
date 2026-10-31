"""
security-headers.py  –  addresses F-05 (missing headers), F-06 (wildcard CORS), F-08 (HSTS)

Python / FastAPI version of the fix. In Cynbit's actual Next.js stack the same headers would be set in
next.config.js or middleware; the controls are identical.

pip install fastapi uvicorn
Run behind a proxy:  uvicorn app:app --no-server-header --proxy-headers
"""
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

# Start with Report-Only, fix violations (Google Analytics etc.), then rename to Content-Security-Policy.
CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' https://www.googletagmanager.com",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https://www.google-analytics.com",
    "connect-src 'self' https://www.google-analytics.com https://*.analytics.google.com",
    "frame-ancestors 'none'",          # anti-clickjacking (modern X-Frame-Options)
    "base-uri 'self'",
    "form-action 'self'",
])

SECURITY_HEADERS = {
    "Content-Security-Policy-Report-Only": CSP,
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    # includeSubDomains/preload only once every subdomain is HTTPS-only
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        return response


def apply_security(app: FastAPI, allowed_origins: list[str]) -> None:
    app.add_middleware(SecurityHeadersMiddleware)
    # Explicit origins instead of "*"
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        allow_credentials=False,
    )


app = FastAPI()
apply_security(app, ["https://www.cynbit.in"])


@app.get("/")
async def home():
    return {"status": "ok"}
