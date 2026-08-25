import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ["DB_NAME"] = "communication_ai_test"

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_DIR / ".env")

import pymongo  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from database import DB_NAME, MONGO_URI  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(scope="session")
def sync_db():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    yield db
    for name in ("users", "messages", "tasks"):
        db[name].delete_many({})
    client.close()


@pytest.fixture(scope="session")
def client(sync_db):
    sync_db.users.create_index("email", unique=True)
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_db(sync_db):
    for name in ("users", "messages", "tasks"):
        sync_db[name].delete_many({})
    yield
    for name in ("users", "messages", "tasks"):
        sync_db[name].delete_many({})
