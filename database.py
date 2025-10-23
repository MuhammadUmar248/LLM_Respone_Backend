import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")

client = AsyncIOMotorClient(MONGODB_URL, tls=True, tlsCAFile=certifi.where())

database = client["alteregodb"]

chat_collection = database["Chat"]

print("✅ MongoDB Connected (alteregodb.Chat)")
