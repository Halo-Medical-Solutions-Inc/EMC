import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict

import pytz
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import analytics, auth, audit_logs, calls, invitations, practice, users, webhooks, websocket
from app.config import settings
from app.database.redis_client import close_redis, get_redis
from app.services.daily_email_service import send_daily_summary_emails
from app.services.publisher_service import CHANNEL_NAME
from app.services.stale_call_service import run_stale_call_recovery_loop
from app.utils.errors import AppError
from app.websocket_manager import manager


DAILY_EMAIL_HOUR = 15
DAILY_EMAIL_MINUTE = 30
DAILY_EMAIL_TIMEZONE = "America/Los_Angeles"


async def redis_subscriber() -> None:
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(CHANNEL_NAME)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await manager.broadcast(data)
                except Exception as e:
                    print(f"Error broadcasting message: {e}")
    except asyncio.CancelledError:
        await pubsub.unsubscribe(CHANNEL_NAME)
        await pubsub.close()


async def daily_email_scheduler() -> None:
    tz = pytz.timezone(DAILY_EMAIL_TIMEZONE)

    while True:
        try:
            now = datetime.now(tz)
            target_time = now.replace(
                hour=DAILY_EMAIL_HOUR,
                minute=DAILY_EMAIL_MINUTE,
                second=0,
                microsecond=0,
            )

            if now >= target_time:
                target_time = target_time + timedelta(days=1)

            wait_seconds = (target_time - now).total_seconds()
            print(
                f"[SCHEDULER] Next daily email at {target_time.strftime('%Y-%m-%d %H:%M %Z')} "
                f"(in {wait_seconds / 3600:.1f} hours)"
            )

            await asyncio.sleep(wait_seconds)

            print("[SCHEDULER] Running daily email job")
            try:
                await send_daily_summary_emails()
            except Exception as e:
                print(f"[SCHEDULER] Error in daily email job: {e}")

            await asyncio.sleep(60)

        except asyncio.CancelledError:
            print("[SCHEDULER] Daily email scheduler stopped")
            break
        except Exception as e:
            print(f"[SCHEDULER] Unexpected error: {e}")
            await asyncio.sleep(300)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    subscriber_task = asyncio.create_task(redis_subscriber())
    stale_recovery_task = asyncio.create_task(run_stale_call_recovery_loop())
    daily_email_task = asyncio.create_task(daily_email_scheduler())

    print("AI Receptionist backend started")

    yield

    subscriber_task.cancel()
    stale_recovery_task.cancel()
    daily_email_task.cancel()

    try:
        await subscriber_task
    except asyncio.CancelledError:
        pass

    try:
        await stale_recovery_task
    except asyncio.CancelledError:
        pass

    try:
        await daily_email_task
    except asyncio.CancelledError:
        pass

    await close_redis()
    print("AI Receptionist backend stopped")


app = FastAPI(
    title="AI Receptionist",
    description="AI-powered medical receptionist for handling inbound calls",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "message": exc.message,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "message": "Internal server error",
        },
    )


app.include_router(analytics.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(invitations.router)
app.include_router(audit_logs.router)
app.include_router(practice.router)
app.include_router(calls.router)
app.include_router(webhooks.router)
app.include_router(websocket.router)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "version": "1.0.0",
            "websocket_connections": manager.get_connection_count(),
        },
        "message": "OK",
    }


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "name": "AI Receptionist",
            "version": "1.0.0",
        },
        "message": "Welcome to AI Receptionist API",
    }
