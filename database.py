import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")

client = None
database = None
chat_collection = None

def get_db():
    global client, database, chat_collection
    if client is None:
        client = AsyncIOMotorClient(MONGODB_URL, tls=True, tlsCAFile=certifi.where())
        database = client["alteregodb"]
        chat_collection = database["Chat"]
    return chat_collection
