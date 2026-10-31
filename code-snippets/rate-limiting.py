import os

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

app = FastAPI()

# Redis is shared between workers. memory:// is only for local testing.
limiter=Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("REDIS_URL", "memory://")
)

app.state.limiter=limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class Newsletter(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: str = Field(max_length=254)
    website: str = Field(default="", max_length=200)
    turnstile_token: str = Field(default="", max_length=2048)


@app.post("/newsletter")
@limiter.limit("3/10 minutes")
def newsletter(request: Request, data: Newsletter):
    if data.website:  # bots may fill this hidden field
        return {"ok": True}

    # Add email validation and optional CAPTCHA verification here.
    return {"ok": True, "message": "Subscription request received"}


@app.post("/contact")
@limiter.limit("5/10 minutes")
def contact(request: Request):
    return {"ok": True, "message": "Inquiry received"}


# Run behind a trusted proxy with correct proxy-header configuration.
# In production, use Redis instead of the in-memory rate-limit store.