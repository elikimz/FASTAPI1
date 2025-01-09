
import time
from typing import Optional
from fastapi import Body, FastAPI, HTTPException,status,Depends
from pydantic import BaseModel
from psycopg2.extras import  RealDictCursor
import psycopg2
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from .import model
from .database import engine,get_db

model.Base.metadata.create_all(bind=engine)

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

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND
        ,detail=f"post with id:{id} does not exist")

    return {"data": dict(test_post)} 
       
    # Return the fetched row directly


@app.get("/test")
def test_posts(db:Session = Depends(get_db)):
     return {"status":"success"}   


@app.post("/createposts")
def create_posts(new_post:posts):
    cursor.execute("""INSERT INTO posts(title,content,published)VALUES(%s,%s,%s)
    RETURNING*""",(new_post.title,new_post.content,new_post.published))
    new_posts=cursor.fetchone()
    conn.commit()
   
    return{"data": new_posts}



   

@app.delete("/posts/{id}")
def delete_posts(id:int):
    cursor.execute("""DELETE FROM posts WHERE id =%s RETURNING *""",(id,))
    deleted_post=cursor.fetchone()
    conn.commit()
    if not deleted_post:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND
        ,detail=f"post with id:{id} does not exist")
    else:
            return {"message": "Post deleted successfully"}


@app.put("/posts/{id}")
def update_posts(id:int,post:posts):
    cursor.execute("""UPDATE  posts SET title=%s,content=%s,published=%s,rating=%s WHERE id=%s RETURNING *""",
    (post.title, post.content, post.published, post.rating ,id))
    updated_posts=cursor.fetchone()
    conn.commit()

    if not updated_posts:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND
        ,detail=f"post with id:{id} does not exist")
    else:
            return {"message": "Post updated successfully", "data": (updated_posts)}

         




   



            