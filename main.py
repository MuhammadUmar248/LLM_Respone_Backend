from fastapi import FastAPI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from bson import ObjectId
from database import get_database

load_dotenv()

app = FastAPI()

# ✅ create DB once & attach to app.state to persist in Vercel
app.state.db = get_database()
chat_collection = app.state.db["Chat"]

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

@app.get("/generate/{prompt_id}")
async def generate_response(prompt_id: str):
    prompt_data = await chat_collection.find_one({"_id": ObjectId(prompt_id)})

    if not prompt_data:
        return {"error": "Prompt not found"}

    result = (prompt | llm | StrOutputParser()).invoke({
        "topicTitle": prompt_data["topicTitle"],
        "question": prompt_data["question"]
    })

    return {
        "prompt_id": prompt_id,
        "prompt": prompt_data["question"],
        "response": result
    }
