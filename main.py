from fastapi import Body, FastAPI
from pydantic import BaseModel
app=FastAPI()

class Post(BaseModel):
    title:str
    content:str


@app.get("/")
def root():
    return {"message": "Welcome to my FASTAPI"}

@app.get("/posts")
def get_posts():
    return{"data":"This is your posts"}

@app.post("/createposts")
def create_posts(payload: dict=Body(...)):
    print(payload)
    return{"new_post": f"title {payload['title']} contet:{payload['content']}"}
            