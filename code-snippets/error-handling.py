import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()
logger=logging.getLogger("app")


def error_response(code: str, message: str, fields=None):
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "fields": fields or {}
        }
    }


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    fields={".".join(str(x) for x in error["loc"][1:]): error["msg"] for error in exc.errors()}
    return JSONResponse(
        status_code=422,
        content=error_response("validation_error", "Please check the submitted data", fields)
    )


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response("http_error", str(exc.detail))
    )


@app.exception_handler(Exception)
async def server_error(request: Request, exc: Exception):
    logger.exception("Error in %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=error_response("server_error", "Something went wrong. Please try again.")
    )


# This set is only for demonstration. In production, use a database UNIQUE constraint.
subscribers=set()


@app.post("/subscribe")
def subscribe(data: dict):
    email=str(data.get("email", "")).strip().lower()

    if not email or "@" not in email:
        return JSONResponse(
            status_code=422,
            content=error_response("validation_error", "Enter a valid email", {"email": "invalid"})
        )

    if email in subscribers:
        return {"ok": True, "message": "Check your inbox to confirm your subscription."}

    subscribers.add(email)
    return {"ok": True, "message": "Check your inbox to confirm your subscription."}


# In production, use SQLAlchemy and handle duplicate emails with a UNIQUE constraint.
# If an IntegrityError occurs, rollback the transaction and return the same success response.