import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from passlib.context import CryptContext

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client.get_default_database()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def migrate_users():
    print("Migrating users collection...")

    users = db.users.find()

    for user in users:
        updates = {}

        # If old UUID field exists, remove it
        if "user_id" in user:
            updates["$unset"] = {"user_id": ""}

        # Add email placeholder if missing
        if "email" not in user:
            fake_email = f"user_{user['_id']}@example.com"
            updates.setdefault("$set", {})["email"] = fake_email

        # Add hashed_password placeholder if missing
        if "hashed_password" not in user:
            hashed = pwd_context.hash("ChangeMe123!")
            updates.setdefault("$set", {})["hashed_password"] = hashed

        # Add created_at if missing
        if "created_at" not in user:
            updates.setdefault("$set", {})["created_at"] = datetime.utcnow()

        if updates:
            db.users.update_one({"_id": user["_id"]}, updates)

    print("Users migration completed.")


def migrate_conversations():
    print("Migrating conversations collection...")

    conversations = db.conversations.find()

    for convo in conversations:

        # If user_id is string UUID, try to map to ObjectId
        if isinstance(convo.get("user_id"), str):

            # Find matching user by old uuid
            old_uuid = convo["user_id"]
            user = db.users.find_one({"user_id": old_uuid})

            if user:
                db.conversations.update_one(
                    {"_id": convo["_id"]},
                    {"$set": {"user_id": user["_id"]}}
                )

    print("Conversations migration completed.")


if __name__ == "__main__":
    migrate_users()
    migrate_conversations()
    print("Schema migration finished successfully.")