from fastapi import FastAPI, HTTPException
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from google.api_core.exceptions import ResourceExhausted
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from bson import ObjectId
from database import get_database
import os

load_dotenv()

app = FastAPI()


# attach DB to app.state to persist across cold starts
app.state.db = get_database()
chat_collection = app.state.db["Chat"]

print("✅ Using MongoDB URL:", os.environ.get("MONGODB_URL") is not None)
print("✅ Using GOOGLE_API_KEY:", os.environ.get("GOOGLE_API_KEY") is not None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM init (sync usage only)
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")
prompt = PromptTemplate(
    input_variables=["topicTitle", "question"],
    template="""
You are an expert chatbot specialized in the topic: "{topicTitle}".

User Question: {question}

Provide a short response (2-3 lines).
"""
)

@app.get("/")
async def root():
    return {"message": "Backend is running ✅"}

@app.get("/test-db")
async def test_db():
    doc = await chat_collection.find_one({})
    return {"ok": True, "sample": str(doc.get("_id")) if doc else None}

@app.get("/generate/{prompt_id}")
async def generate_response(prompt_id: str):
    try:
        if not ObjectId.is_valid(prompt_id):
            raise HTTPException(status_code=400, detail="Invalid prompt_id format")

        prompt_data = await chat_collection.find_one({"_id": ObjectId(prompt_id)})
        if not prompt_data:
            raise HTTPException(status_code=404, detail="Prompt not found")

        # runnable pipeline (sync)
        runnable_chain = prompt | llm | StrOutputParser()
        inputs = {
            "topicTitle": prompt_data.get("topicTitle", ""),
            "question": prompt_data.get("question", "")
        }

        # ✅ run synchronously in its own thread (safe on Vercel)
        def run_sync():
            return runnable_chain.invoke(inputs)

        result = await asyncio.to_thread(run_sync)

        return {
            "prompt_id": prompt_id,
            "prompt": prompt_data.get("question", ""),
            "response": result
        }

    except ResourceExhausted:
        raise HTTPException(
            status_code=429,
            detail="Free tier quota exceeded. Please wait 20-30 seconds and try again."
        )
    except Exception as e:
        print("❌ Error in /generate:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))
