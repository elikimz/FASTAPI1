import time
from typing import Optional
from fastapi import Body, FastAPI
from pydantic import BaseModel
from psycopg2.extras import  RealDictCursor
import psycopg2

app=FastAPI()

class posts(BaseModel):
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
    cursor.execute("""SELECT * FROM posts""")
    posts=cursor.fetchall()
    # print(posts)
    return{"data":posts}


@app.get("/posts/{id}")
def get_posts(id: int):
    cursor.execute("""SELECT * FROM posts WHERE id = %s""", (id,))
    test_post = cursor.fetchone()

    if not test_post:
        return {"error": "Post not found"}, 404

    # Return the fetched row directly
    return {"data": dict(test_post)}


@app.post("/createposts")
def create_posts(new_post:posts):
    cursor.execute("""INSERT INTO posts(title,content,published)VALUES(%s,%s,%s)
    RETURNING*""",(new_post.title,new_post.content,new_post.published))
    new_posts=cursor.fetchone()
    conn.commit()
   
    return{"data": new_posts}
            