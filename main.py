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

# create DB once & attach to app.state to persist in Vercel
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

# LLM (make sure GOOGLE_API_KEY is set in env)
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

        # Build the runnable pipeline once
        runnable_chain = prompt | llm | StrOutputParser()
        inputs = {
            "topicTitle": prompt_data.get("topicTitle", ""),
            "question": prompt_data.get("question", "")
        }

        # 1) Preferred: run the runnable asynchronously in the current event loop
        try:
            result = await runnable_chain.ainvoke(inputs)
        except Exception as e_async:
            # If the async path fails (for example "Event loop is closed" or other RuntimeErrors),
            # fall back to executing in a separate thread with a fresh event loop.
            print("⚠️ async invoke failed, falling back to thread():", repr(e_async))

            def thread_fn():
                # Create and use a fresh event loop inside the thread to avoid "Event loop is closed" errors
                import asyncio as _asyncio
                loop = _asyncio.new_event_loop()
                _asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(runnable_chain.ainvoke(inputs))
                finally:
                    try:
                        loop.close()
                    except Exception:
                        pass

            result = await asyncio.to_thread(thread_fn)

        # Ensure result is serializable
        if hasattr(result, "__dict__"):
            # best-effort conversion
            result = str(result)

        return {
            "prompt_id": prompt_id,
            "prompt": prompt_data.get("question", ""),
            "response": result
        }

    except HTTPException:
        raise
    except Exception as e:
        print("❌ Error in /generate:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))
