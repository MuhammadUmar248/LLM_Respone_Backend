import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = "alteregodb"

# ✅ Global cached client to prevent reconnection on every request
_client = None

def get_db_client():
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URL, tls=True, tlsCAFile=certifi.where())
    return _client

client = get_db_client()
database = client[DATABASE_NAME]
chat_collection = database["Chat"]

print("✅ MongoDB Connected (alteregodb.Chat)")
