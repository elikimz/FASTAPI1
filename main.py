import time
from typing import Optional
from fastapi import Body, FastAPI
from pydantic import BaseModel
from psycopg2.extras import  RealDictCursor
import psycopg2

app=FastAPI()

class Posts(BaseModel):
    title:str
    content:str
    published:bool=True
    rating:Optional[int]=None


try:
     conn = psycopg2.connect(host='localhost', database='postgres',user="postgres", password='40284433',
     cursor_factory=RealDictCursor)
     cursor = conn.cursor()
     print("Database connected successfully")
except Exception as error:
    print("Connection to database failed") 
    print("Error:",error) 
    time.sleep(2)   



@app.get("/")
def root():
    return {"message": "Welcome to my FASTAPI"}

@app.get("/posts")
def get_posts():
    return{"data":"This is your posts"}

@app.post("/createposts")
def create_posts(new_post:Posts):
    print(new_post.dict())
    return{"data": new_post}
            