from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from database import engine, get_db
from sqlalchemy import text
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from openai import OpenAI
import re


def clean_query(query: str) -> str:
    """
    Cleans the AI-generated SQL query by removing code block markers and extra whitespace.
    """
    # Remove code block markers if present
    query = re.sub(r"^```sql\s*|^```", "", query, flags=re.IGNORECASE)
    query = re.sub(r"```$", "", query)
    # Remove leading/trailing whitespace
    return query.strip()




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


@app.post("/clients")
def clients(request: dict, db: Session = Depends(get_db)):
    user_question = request.get("question")
    if not user_question:
        raise HTTPException(status_code=400, detail="No question provided")

    # Step 1: AI generates SQL
    prompt = f"""
    You are an assistant that converts plain English questions into SQL queries.
    The database has a table called 'tb_Client'.
    
    Question: {user_question}
    
    Return only a valid SQL SELECT query (no explanation).
    """
    ai_sql = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    ).choices[0].message.content.strip()

    ai_sql = clean_query(ai_sql)

    # Step 2: Safety check
    if not ai_sql.lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")

    # Step 3: Execute
    try:
        result = db.execute(text(ai_sql)).fetchall()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL error: {str(e)}")

    rows = [dict(row._mapping) for row in result]

    # Step 4: AI explains result
    explanation_prompt = f"""
    The user asked: {user_question}
    The SQL run was: {ai_sql}
    The result was: {rows[:5]} (showing first 5 rows only)
    
    Write a short explanation of this result in plain English.
    """
    explanation = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": explanation_prompt}],
        temperature=0
    ).choices[0].message.content.strip()

    return {
        "question": user_question,
        "sql": ai_sql,
        "result": rows,
        "explanation": explanation
    }

