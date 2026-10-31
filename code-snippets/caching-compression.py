import hashlib
import json
import time

from brotli_asgi import BrotliMiddleware
from fastapi import BackgroundTasks, FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Compress responses to reduce the amount of data sent to the browser.
app.add_middleware(BrotliMiddleware, quality=4, minimum_size=500, gzip_fallback=True)


class StaticFilesCache(StaticFiles):
    async def get_response(self, path, scope):
        response=await super().get_response(path, scope)

        if response.status_code == 200:
            response.headers["Cache-Control"]="public, max-age=31536000, immutable"

        return response


# Enable this when a static directory is available.
# app.mount("/static", StaticFilesCache(directory="static"), name="static")


@app.get("/blog")
def blog(request: Request):
    data={"posts": [{"slug": "ai-first-learning", "title": "AI-first learning"}]}
    etag='"' + hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16] + '"'

    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})

    return Response(
        content=json.dumps(data),
        media_type="application/json",
        headers={
            "ETag": etag,
            "Cache-Control": "public, max-age=60, stale-while-revalidate=300"
        }
    )


@app.middleware("http")
async def no_cache_for_write_requests(request: Request, call_next):
    response=await call_next(request)

    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        response.headers["Cache-Control"]="no-store"

    return response


def send_email(inquiry_id: int):
    time.sleep(2)  # example delay for an email or CRM request


@app.post("/contact")
def contact(background: BackgroundTasks):
    inquiry_id=1  # replace this with the ID returned by the database
    background.add_task(send_email, inquiry_id)

    return {"ok": True, "message": "Inquiry received"}


# For production, use Celery, RQ or another queue if tasks need retries and monitoring.