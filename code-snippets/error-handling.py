"""
error-handling.py  –  addresses F-02 (duplicates) and observation that failures are hard to monitor

pip install fastapi
One error envelope for every failure, real HTTP status codes (so monitoring can count them),
no submitted data echoed back, and generic messages to users with details only in server logs.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app")
app = FastAPI()


def error_body(code: str, message: str, fields: dict | None = None) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, "fields": fields or {}}}


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    # FastAPI's default response echoes the submitted values; return only field name + message.
    fields = {".".join(str(p) for p in err["loc"][1:]): err["msg"] for err in exc.errors()}
    return JSONResponse(status_code=422, content=error_body("validation_error", "Please check the form", fields))


@app.exception_handler(StarletteHTTPException)
async def http_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content=error_body("http_error", str(exc.detail)))


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    logger.exception("unhandled error on %s %s", request.method, request.url.path)  # details stay in logs
    return JSONResponse(status_code=500, content=error_body("server_error", "Something went wrong. Please try again."))


# --- Duplicate handling (idempotent subscribe) -------------------------------------------------------
_subscribers: set[str] = set()   # stand-in for a table with a UNIQUE index on email


@app.post("/subscribe")
async def subscribe(payload: dict):
    email = str(payload.get("email", "")).strip().lower()
    if not email or "@" not in email:
        return JSONResponse(status_code=422, content=error_body("validation_error", "Enter a valid e-mail", {"email": "invalid"}))
    if email in _subscribers:
        # Same message as a new signup -> an attacker cannot learn who is already subscribed.
        return {"ok": True, "message": "Check your inbox to confirm your subscription."}
    _subscribers.add(email)
    return {"ok": True, "message": "Check your inbox to confirm your subscription."}

# With SQLAlchemy, rely on the database constraint instead of check-then-insert:
#   try:
#       session.add(Subscriber(email=email)); session.commit()
#   except IntegrityError:
#       session.rollback()           # already subscribed -> treat as success
