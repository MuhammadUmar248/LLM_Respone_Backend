import certifi
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGODB_URL = os.environ.get("MONGODB_URL")  # ✅ Production safe
DATABASE_NAME = "alteregodb"

def get_database():
    if not MONGODB_URL:
        raise Exception("❌ MONGODB_URL is not set")
    client = AsyncIOMotorClient(MONGODB_URL, tls=True, tlsCAFile=certifi.where())
    return client[DATABASE_NAME]
