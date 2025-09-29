from fastapi import FastAPI, Depends
from pydantic import BaseModel
from database import engine, get_db
from sqlalchemy import text
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI() 

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(request: ChatRequest):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": request.message}
        ]
    )
    return {"response": response.choices[0].message.content}


@app.on_event("startup")
def startup_event():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sys.databases"))
            dbs = [row[0] for row in result]
            print("✅ Connected to SQL Server. Databases:", dbs)
    except Exception as e:
        print("❌ DB connection failed:", e)


@app.get("/")
async def root():
    return {"message": "welcome to hosibill"}   


@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT name FROM sys.databases"))
    return [row[0] for row in result]


@app.get("/tables")
def list_tables(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"))
    return [row[0] for row in result]


