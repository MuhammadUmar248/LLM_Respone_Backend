from fastapi import FastAPI
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
        # ✅ 1. Check valid ObjectId
        if not ObjectId.is_valid(prompt_id):
            return {"error": "Invalid prompt_id format"}

        # ✅ 2. Fetch record from DB
        prompt_data = await chat_collection.find_one({"_id": ObjectId(prompt_id)})
        if not prompt_data:
            return {"error": "Prompt not found"}

        # ✅ 3. Call LLM (async recommended in FastAPI)
        result = await (prompt | llm | StrOutputParser()).ainvoke({
            "topicTitle": prompt_data.get("topicTitle", ""),
            "question": prompt_data.get("question", "")
        })

        # ✅ 4. Return clean response
        return {
            "prompt_id": prompt_id,
            "prompt": prompt_data.get("question", ""),
            "response": result
        }

    except Exception as e:
        print("❌ Error inside /generate route:", e)
        raise HTTPException(status_code=500, detail=str(e))

