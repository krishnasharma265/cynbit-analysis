"""
rate-limiting.py  –  addresses F-04 (no anti-automation control)

pip install fastapi slowapi httpx
Use a shared store in production:  REDIS_URL=redis://...  (default is in-memory, one process only)
Behind a proxy/CDN start uvicorn with --proxy-headers so the real client IP is used.
"""
import os

import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, storage_uri=os.getenv("REDIS_URL", "memory://"))

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # returns HTTP 429

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class NewsletterIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    email: str = Field(max_length=254)
    website: str = Field(default="", max_length=200)   # honeypot: humans leave it empty
    turnstile_token: str = Field(default="", max_length=2048)


async def verify_turnstile(token: str, ip: str) -> bool:
    """Cloudflare Turnstile: render the widget in the page, send its token with the form."""
    if not token:
        return False
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.post(
            TURNSTILE_VERIFY_URL,
            data={"secret": os.environ["TURNSTILE_SECRET_KEY"], "response": token, "remoteip": ip},
        )
    return resp.json().get("success") is True


@app.post("/newsletter")
@limiter.limit("3/10 minutes")           # per client IP; stricter than the contact form
async def newsletter(request: Request, payload: NewsletterIn):
    if payload.website:                  # honeypot
        return {"ok": True}
    if os.getenv("TURNSTILE_SECRET_KEY") and not await verify_turnstile(
        payload.turnstile_token, get_remote_address(request)
    ):
        raise HTTPException(status_code=400, detail="Captcha verification failed")
    return {"ok": True}


@app.post("/contact")
@limiter.limit("5/10 minutes")
async def contact(request: Request):
    return {"ok": True}

# Several actions can share one URL in a framework (Cynbit's newsletter and contact both POST to /contact),
# so key limits by action name or endpoint, not only by path.
