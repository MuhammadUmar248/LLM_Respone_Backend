import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = "alteregodb"

def get_database():
    client = AsyncIOMotorClient(MONGODB_URL, tls=True, tlsCAFile=certifi.where())
    db = client[DATABASE_NAME]
    return db
