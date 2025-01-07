from fastapi import FastAPI
app=FastAPI()
@app.get("/")
def root():
    return {"message": "Welcome to my FASTAPI"}

@app.get("/posts")
def get_posts():
    return{"data":"This is your posts"}
@app.post("/createposts")
def create_posts():
    return{"data":"posts created successifully"}
            