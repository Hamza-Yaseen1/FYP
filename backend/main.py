from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

from database import users_collection, messages_collection, tasks_collection
from routes.auth import router as auth_router
from routes.messages import router as messages_router
from routes.webhooks import router as webhooks_router
from routes.tasks import router as tasks_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await users_collection.create_index("email", unique=True)
    await messages_collection.create_index([("user_id", 1), ("created_at", -1)])
    await tasks_collection.create_index([("user_id", 1), ("created_at", -1)])
    yield


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


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(messages_router)
app.include_router(webhooks_router)
app.include_router(tasks_router)
