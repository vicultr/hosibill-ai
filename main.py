from fastapi import FastAPI, Body
from pydantic import BaseModel

app = FastAPI() 

class Item(BaseModel):
    title: str
    content: str

@app.get("/")
async def root():
    return {"message": "welcome to hosibill"}   

@app.post("/items")
def create_item(item: Item):
    item.dict()
    return {"item": item}

# title str, content str