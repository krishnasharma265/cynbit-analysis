import os
from datetime import date, timedelta

from email_validator import EmailNotValidError, validate_email
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field, field_validator

app = FastAPI()

CHECK_EMAIL_DNS=os.getenv("CHECK_EMAIL_DNS", "1") == "1"
MOBILE_CORE=r"(?:\+91|91|0)?[6-9]\d{9}"


def normalize_email(email: str):
    try:
        return validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError as e:
        raise ValueError(str(e))


class Contact(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True, extra="forbid")

    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(max_length=254)
    company: str = Field(default="", max_length=120)
    industry: str = Field(default="", max_length=80)
    message: str = Field(min_length=10, max_length=2000)
    website: str = Field(default="", max_length=200)

    @field_validator("email")
    @classmethod
    def validate_email_address(cls, value):
        return normalize_email(value)


class Career(BaseModel):
    model_config=ConfigDict(str_strip_whitespace=True, extra="forbid")

    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(max_length=254)
    mobile: str = Field(pattern=f"^{MOBILE_CORE}$")
    whatsapp: str = Field(default="", pattern=f"^(?:{MOBILE_CORE})?$")
    dob: date
    agreed_to_terms: bool

    @field_validator("email")
    @classmethod
    def validate_email_address(cls, value):
        return normalize_email(value)

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, value):
        today=date.today()
        if not (today - timedelta(days=365 * 70) <= value <= today - timedelta(days=365 * 16)):
            raise ValueError("Please check your date of birth")
        return value

    @field_validator("agreed_to_terms")
    @classmethod
    def validate_terms(cls, value):
        if not value:
            raise ValueError("Please accept the terms")
        return value


# DNS check can be disabled for offline testing.
async def check_email_dns(email: str):
    if not CHECK_EMAIL_DNS:
        return

    try:
        await run_in_threadpool(validate_email, email, check_deliverability=True)
    except EmailNotValidError:
        raise HTTPException(status_code=422, detail={"email": "This email domain cannot receive mail"})


@app.post("/contact")
async def contact(data: Contact):
    if data.website:  # honeypot field used to catch simple bots
        return {"ok": True}

    await check_email_dns(data.email)
    # Save inquiry in database here.
    return {"ok": True, "message": "Inquiry received"}


@app.post("/careers/apply")
async def apply(data: Career):
    await check_email_dns(data.email)
    # Save application in database here.
    return {"ok": True, "message": "Application received"}