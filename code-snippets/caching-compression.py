"""
caching-compression.py  –  addresses F-10 (slow form responses) and F-11 (heavy payloads)

pip install fastapi brotli-asgi
"""
import hashlib
import json
import time

from brotli_asgi import BrotliMiddleware
from fastapi import BackgroundTasks, FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 1) Compression: Brotli with gzip fallback for clients that do not send "br"
app.add_middleware(BrotliMiddleware, quality=4, minimum_size=500, gzip_fallback=True)


# 2) Static assets: fingerprinted files can be cached "forever"
class ImmutableStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

# app.mount("/static", ImmutableStaticFiles(directory="static"), name="static")


# 3) Public GET data: ETag + short cache, so repeat visits get "304 Not Modified"
@app.get("/blog")
async def blog(request: Request, response: Response):
    body = {"posts": [{"slug": "ai-first-learning", "title": "AI-first learning"}]}
    etag = '"' + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16] + '"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return body


# 4) Form submissions: never cache, and do the slow work AFTER responding
@app.middleware("http")
async def no_store_for_writes(request: Request, call_next):
    response = await call_next(request)
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        response.headers["Cache-Control"] = "no-store"
    return response


def send_notification_email(inquiry_id: int) -> None:
    time.sleep(2)  # stands in for SMTP / CRM call that made the request slow


@app.post("/contact")
async def contact(background: BackgroundTasks):
    inquiry_id = 1                                    # 1) one fast, indexed DB write
    background.add_task(send_notification_email, inquiry_id)  # 2) slow part runs after the response
    return {"ok": True}                               # user gets an answer in milliseconds
# Production: use a real queue (Celery, RQ, arq) so failed e-mails are retried.
