from fastapi import FastAPI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from database import chat_collection
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from bson import ObjectId




load_dotenv()
 
app = FastAPI()

origins = [
    "http://localhost:3000",  
    # "https://your-frontend-domain.vercel.app"  # deployed frontend (if applicable)
]
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

The user is asking a question related to this topic.

User Question: {question}

Please provide a helpful, clear, accurate, and topic-focused response.
If the user greets (like "hi" or "hello"), introduce yourself as a chatbot for this topic.
Response Rules:
- Keep the response short (2-3 lines max)
- Be clear, practical, and beginner-friendly
- If the user greets (e.g., "hi" or "hello"), introduce yourself as a chatbot for this topic
- If applicable, provide only the **best** method or **one main approach**, not multiple long explanations

Now provide the answer based on the topic above:



"""
)


@app.get("/")
async def root():
    return {"message": "Backend is running ✅"}

@app.get("/generate/{prompt_id}")
async def generate_response(prompt_id: str):
    # 1️⃣ Fetch prompt from DB

    prompt_data = await chat_collection.find_one({"_id": ObjectId(prompt_id)})


    print(prompt_data)
    
    if not prompt_data:
        return {"error": "Prompt not found"}

    prompt_question = prompt_data["question"]
    prompt_topic = prompt_data["topicTitle"]
  

    parser = StrOutputParser()
    chain = prompt | llm | parser

    result = chain.invoke({"topicTitle":  prompt_topic, "question": prompt_question})

    return {
        "prompt_id": prompt_id,
        "prompt": prompt_question,
        "response": result
    }
