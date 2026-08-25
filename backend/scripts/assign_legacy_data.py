"""Assign all legacy messages/tasks (missing user_id) to one user.

Usage:
    python scripts/assign_legacy_data.py --email hamza@example.com

Idempotent: documents that already have a user_id are left untouched.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import pymongo  # noqa: E402

from database import DB_NAME, MONGO_URI  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assign legacy messages/tasks to a user by email."
    )
    parser.add_argument("--email", required=True, help="Target user's email")
    args = parser.parse_args()

    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]

    user = db.users.find_one({"email": args.email.lower()})
    if not user:
        print(f"Error: no user found with email '{args.email}'")
        return 1

    uid = str(user["_id"])
    query = {"user_id": {"$exists": False}}

    msg_result = db.messages.update_many(query, {"$set": {"user_id": uid}})
    task_result = db.tasks.update_many(query, {"$set": {"user_id": uid}})

    print(f"Assigned {msg_result.modified_count} message(s) to {args.email}")
    print(f"Assigned {task_result.modified_count} task(s) to {args.email}")

    client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
