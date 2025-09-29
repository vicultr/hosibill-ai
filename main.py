from fastapi import FastAPI, Depends
from pydantic import BaseModel
from database import engine, get_db
from sqlalchemy import text
from sqlalchemy.orm import Session


app = FastAPI() 


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

