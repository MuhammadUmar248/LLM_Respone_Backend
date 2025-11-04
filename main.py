from fastapi import FastAPI, HTTPException
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from bson import ObjectId
from database import get_database
import os

load_dotenv()

app = FastAPI()

# Attach DB once on startup
app.state.db = get_database()
chat_collection = app.state.db["Chat"]
topic_collection = app.state.db["Topic"]

print("✅ MongoDB Connected:", bool(os.environ.get("MONGODB_URL")))
print("✅ Google API Key Loaded:", bool(os.environ.get("GOOGLE_API_KEY")))

# Allow all origins for CORS (safe for dev — restrict later if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM (Google Gemini)
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")

prompt = PromptTemplate(
    input_variables=["topicTitle", "question", "instructions"],
    template=(
        "You are an expert chatbot specialized in the topic: '{topicTitle}'.\n\n"
        "User Question: {question}\n\n"
        "Follow these instructions: {instructions}\n"
        "Provide a short, clear answer (1–2 sentences)."
    )
)

@app.get("/")
async def root():
    return {"message": "Backend is running ✅"}

@app.get("/test-db")
async def test_db():
    doc = await chat_collection.find_one({})
    return {"ok": True, "sample": str(doc.get('_id')) if doc else None}

@app.get("/generate/{topic_id}")
async def generate_response(topic_id: str):
    try:
        if not ObjectId.is_valid(topic_id):
            raise HTTPException(status_code=400, detail="Invalid topic_id format")

        topic_data = await topic_collection.find_one({"_id": ObjectId(topic_id)})
        if not topic_data:
            raise HTTPException(status_code=404, detail="Topic not found")

        latest_chat = await chat_collection.find_one(
            {"topicId": ObjectId(topic_id), "from": "user"},
            sort=[("createdAt", -1)]
        )

        if not latest_chat:
            raise HTTPException(status_code=404, detail="No user messages found")

        print("✅ Topic:", topic_data.get("title"))
        print("✅ Latest Chat:", latest_chat.get("text"))

        runnable_chain = prompt | llm | StrOutputParser()

        inputs = {
            "topicTitle": topic_data.get("title", ""),
            "question": latest_chat.get("text", ""),
            "instructions": topic_data.get("instructions", "")
        }

        # Run safely in async environment
        result = await asyncio.to_thread(runnable_chain.invoke, inputs)

        return {
            "topic_id": topic_id,
            "response": result
        }

    except HTTPException:
        raise
    except Exception as e:
        print("❌ Error in /generate:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))
