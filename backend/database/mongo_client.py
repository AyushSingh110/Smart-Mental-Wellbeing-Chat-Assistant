from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings


class MongoClient:

    def __init__(self):
        self.client = AsyncIOMotorClient(
            settings.MONGO_URI,
            tls=True,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            maxPoolSize=10,
        )
        self.db = self.client[settings.MONGO_DB_NAME]
        self.conversations = self.db["conversations"]
        self.users = self.db["users"]

    async def get_recent_conversations(self, user_id: str, limit: int = 50):
        cursor = (
            self.conversations.find({"user_id": user_id})
            .sort("timestamp", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def close(self):
        self.client.close()