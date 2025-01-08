from fastapi import Body, FastAPI
from pydantic import BaseModel
app=FastAPI()

class Posts(BaseModel):
    title:str
    content:str
    published:bool=True


@app.get("/")
def root():
    return {"message": "Welcome to my FASTAPI"}

@app.get("/posts")
def get_posts():
    return{"data":"This is your posts"}

@app.post("/createposts")
def create_posts(new_post:Posts):
    print(new_post)
    return{"data": "new_post"}
            