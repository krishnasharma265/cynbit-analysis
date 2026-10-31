"""
input-validation.py  –  addresses F-01 (unreal e-mails), F-02 (no length limits), F-03 (unverified personal data)

pip install fastapi pydantic email-validator

Key point: syntax checks alone ACCEPT "name@gmail.commmm" (it looks like a valid domain).
Only a DNS/deliverability check (or, best, a confirmation e-mail / double opt-in) rejects it.
"""
import os
from datetime import date, timedelta

from email_validator import EmailNotValidError, validate_email
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Turn off only in offline tests
CHECK_EMAIL_DNS = os.getenv("CHECK_EMAIL_DNS", "1") == "1"
MOBILE_CORE = r"(?:\+91|91|0)?[6-9]\d{9}"


def _normalize_email(value: str) -> str:
    try:
        return validate_email(value, check_deliverability=False).normalized  # syntax only
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc


class ContactIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")  # unknown fields rejected

    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(max_length=254)
    company: str = Field(default="", max_length=120)
    industry: str = Field(default="", max_length=80)
    message: str = Field(min_length=10, max_length=2000)
    website: str = Field(default="", max_length=200)  # honeypot: humans leave it empty

    @field_validator("email")
    @classmethod
    def check_email_syntax(cls, v: str) -> str:
        return _normalize_email(v)


class CareerIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(max_length=254)
    mobile: str = Field(pattern=f"^{MOBILE_CORE}$")
    whatsapp: str = Field(default="", pattern=f"^(?:{MOBILE_CORE})?$")
    dob: date
    agreed_to_terms: bool

    @field_validator("email")
    @classmethod
    def check_email_syntax(cls, v: str) -> str:
        return _normalize_email(v)

    @field_validator("dob")
    @classmethod
    def plausible_dob(cls, v: date) -> date:
        today = date.today()
        if not (today - timedelta(days=365 * 70) <= v <= today - timedelta(days=365 * 16)):
            raise ValueError("Please check your date of birth")
        return v

    @field_validator("agreed_to_terms")
    @classmethod
    def must_agree(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Please accept the terms")
        return v


async def ensure_deliverable(email: str) -> None:
    """DNS check (MX/A record). Blocking I/O, so run it in a thread pool."""
    if not CHECK_EMAIL_DNS:
        return
    try:
        await run_in_threadpool(validate_email, email, check_deliverability=True)
    except EmailNotValidError:
        raise HTTPException(status_code=422, detail={"email": "This e-mail domain cannot receive mail"})


app = FastAPI()


@app.post("/contact")
async def contact(payload: ContactIn):
    if payload.website:            # honeypot filled -> bot; pretend success, store nothing
        return {"ok": True}
    await ensure_deliverable(payload.email)
    # save to DB, then send a confirmation link (double opt-in) for newsletters
    return {"ok": True}


@app.post("/careers/apply")
async def apply(payload: CareerIn):
    await ensure_deliverable(payload.email)
    return {"ok": True}
