import asyncio
import os

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv
import logging


from pymongo import MongoClient
from database import users_collection, messages_collection, tasks_collection, connections_collection, create_indexes, DB_NAME
from routes.auth import router as auth_router
from routes.messages import router as messages_router
from routes.webhooks import router as webhooks_router
from routes.tasks import router as tasks_router
from routes.connections import router as connections_router
from routes.gmail import router as gmail_router, google_router
from routes.analytics import router as analytics_router
from routes.test import router as test_router  # TEMPORARY - for load testing

load_dotenv()

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await users_collection.create_index("email", unique=True)
    await messages_collection.create_index([("user_id", 1), ("created_at", -1)])
    await messages_collection.create_index(
        [("sender", "text"), ("content", "text"), ("ai_analysis.summary", "text")],
        background=True,
    )
    # Eliminate the legacy global dedupe index (external_message_id alone) —
    # a cross-user key collision would block a legitimately-distinct second
    # user's same-key document. Replace with the user-scoped composite.
    try:
        await messages_collection.drop_index("external_message_id_1")
    except Exception:
        pass
    await messages_collection.create_index(
        [("user_id", 1), ("external_message_id", 1)],
        unique=True,
        partialFilterExpression={"external_message_id": {"$type": "string"}},
    )
    await messages_collection.create_index(
        [("user_id", 1), ("conversationId", 1), ("received_at", -1)]
    )
    await messages_collection.create_index(
        [("user_id", 1), ("threadId", 1), ("received_at", -1)]
    )
    # Counts/filter hot paths: user-scoped priority/status selects are covered
    # by compound indexes instead of scanning every message of the user.
    await messages_collection.create_index(
        [("user_id", 1), ("ai_analysis.priority", 1), ("created_at", -1)]
    )
    await messages_collection.create_index(
        [("user_id", 1), ("status", 1), ("created_at", -1)]
    )
    # Source dropdowns / source filters.
    await messages_collection.create_index(
        [("user_id", 1), ("source", 1), ("created_at", -1)]
    )
    await tasks_collection.create_index([("user_id", 1), ("created_at", -1)])
    await connections_collection.create_index(
        [("user_id", 1), ("provider", 1)],
        unique=True
    )
    await connections_collection.create_index([("user_id", 1)])
    await create_indexes()

    # Start Gmail poller if credentials are configured (skip the test DB —
    # the poller would hit Google with throwaway test tokens every cycle)
    _gmail_poller_task = None
    if os.getenv("GOOGLE_CLIENT_ID") and DB_NAME != "communication_ai_test":
        from services.gmail import poll_connected_gmail

        async def _gmail_poll_loop():
            interval = int(os.getenv("GMAIL_POLL_INTERVAL_SECONDS", "30"))
            logger.info("Gmail poller started (interval=%ds)", interval)
            while True:
                try:
                    await poll_connected_gmail()
                except Exception:
                    logger.exception("Gmail poller cycle failed")
                await asyncio.sleep(interval)

        _gmail_poller_task = asyncio.create_task(_gmail_poll_loop())

    # Retry-pending sweep for AI analyses that degraded to status="pending"
    # during an outage. Skipped on the test DB so suites call
    # retry_pending_analyses directly.
    _retry_pending_task = None
    if DB_NAME != "communication_ai_test":
        from services.retry_pending import retry_pending_analyses

        async def _retry_pending_loop():
            interval = int(os.getenv("RETRY_INTERVAL_SECONDS", "60"))
            logger.info("Pending-analysis retry loop started (interval=%ds)", interval)
            while True:
                try:
                    await retry_pending_analyses()
                except Exception:
                    logger.exception("Pending-analysis retry cycle failed")
                await asyncio.sleep(interval)

        _retry_pending_task = asyncio.create_task(_retry_pending_loop())

    yield

    # Shut down pollers
    if _gmail_poller_task is not None:
        _gmail_poller_task.cancel()
        try:
            await _gmail_poller_task
        except asyncio.CancelledError:
            pass
    if _retry_pending_task is not None:
        _retry_pending_task.cancel()
        try:
            await _retry_pending_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Communication AI Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compress JSON payloads >1KB (messages lists, analytics) before they hit the
# wire. Added after CORS so the CORS headers survive the gzip rewrite.
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.get("/")
def read_root():
    return {"message":"Backend is running "}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/test-db")
def test_db():
    try:

        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        client = MongoClient(mongo_uri)
        client.admin.command("ping")
        return {"message": "MongoDB is connected successfully"}
    except Exception as e:
        return {"error": str(e)}

app.include_router(auth_router)
app.include_router(messages_router)
app.include_router(webhooks_router)
app.include_router(tasks_router)
app.include_router(connections_router)
app.include_router(gmail_router)
app.include_router(google_router)
app.include_router(analytics_router)
app.include_router(test_router)  # TEMPORARY - for load testing
