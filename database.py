import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = "alteregodb"
# MongoDB connection
client = AsyncIOMotorClient(MONGODB_URL, tls=True, tlsCAFile=certifi.where())
database = client[DATABASE_NAME]
chat_collection = database["Chat"]
