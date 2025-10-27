from fastapi import FastAPI
import asyncio
from fastapi import HTTPException
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

# ✅ create DB once & attach to app.state to persist in Vercel
app.state.db = get_database()
chat_collection = app.state.db["Chat"]

print("✅ Using MongoDB URL:", os.environ.get("MONGODB_URL") is not None)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

from bson import ObjectId
from fastapi import HTTPException

@app.get("/generate/{prompt_id}")
async def generate_response(prompt_id: str):
    try:
        if not ObjectId.is_valid(prompt_id):
            raise HTTPException(status_code=400, detail="Invalid prompt_id format")

        prompt_data = await chat_collection.find_one({"_id": ObjectId(prompt_id)})
        if not prompt_data:
            raise HTTPException(status_code=404, detail="Prompt not found")

        # ✅ RUN LLM IN A THREAD (important for Vercel)
        async def run_llm():
            return await (prompt | llm | StrOutputParser()).ainvoke({
                "topicTitle": prompt_data.get("topicTitle", ""),
                "question": prompt_data.get("question", "")
            })

        result = await asyncio.to_thread(asyncio.run, run_llm())

        return {
            "prompt_id": prompt_id,
            "prompt": prompt_data.get("question", ""),
            "response": result
        }

    except Exception as e:
        print("❌ Error in /generate:", e)
        raise HTTPException(status_code=500, detail=str(e))