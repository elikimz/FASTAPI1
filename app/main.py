
import time
from fastapi import Body, FastAPI, HTTPException,status,Depends
from psycopg2.extras import  RealDictCursor
import psycopg2
from sqlalchemy.orm import Session
from .import models,schemas,utils
from .database import engine,get_db
from sqlalchemy import Engine



models.Base.metadata.create_all(bind=engine)


app=FastAPI()







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

@app.get("/posts",response_model=list[schemas.Post])
def get_posts(db:Session = Depends(get_db)):
    
    posts=db.query(models.Post).all()
    # print(posts)
    return posts


@app.get("/posts/{id}")
def get_posts(id: int,db:Session = Depends(get_db)):
   test_post= db.query(models.Post).filter(models.Post.id== id).first()
   print(test_post)

   

   if not test_post:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND
        ,detail=f"post with id:{id} does not exist")

   return  test_post 
       
    # Return the fetched row directly

 


@app.post("/createposts",response_model=schemas.Post)
def create_posts(new_post:schemas.PostCreate,db:Session = Depends(get_db)):
  new_posts= models.Post(
       **new_post.dict()
  )
  db.add(new_posts) 
  db.commit()
  db.refresh(new_posts)
   
  return new_posts



   

@app.delete("/posts/{id}")
def delete_posts(id:int,db:Session = Depends(get_db)):
    
    deleted_post=db.query(models.Post).filter(models.Post.id== id).first()
    
    if not deleted_post:
             
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND
        ,detail=f"post with id:{id} does not exist")
    db.delete(deleted_post)
    db.commit()

    return "post deleted successifully"

   


@app.put("/posts/{id}")
def update_posts(id:int,post:schemas.PostUpdate,db:Session = Depends(get_db)):

    updated_query=db.query(models.Post).filter(models.Post.id == id)
    existing_post =updated_query.first()


  
    if not existing_post:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND
        ,detail=f"post with id:{id} does not exist")
    
    
    updated_query.update(post.dict(),synchronize_session=False)

    db.commit()
    db.refresh(existing_post)
    return    existing_post

   

         




# user path operation

@app.post("/users",status_code=status.HTTP_201_CREATED,response_model=schemas.UserResponse)
def create_user(new_user:schemas.UserCreate, db:Session = Depends(get_db)):
     
     hashed_password=utils.hash(new_user.password)
     new_user.password=hashed_password
     new_user= models.User(
       **new_user.dict()
    )
     db.add(new_user) 
     db.commit()
     db.refresh(new_user)
   
     return new_user
   



@app.get('/users/{id}',response_model=schemas.UserResponse)
def get_user(id:int,db:Session = Depends(get_db)):
    user=db.query(models.User).filter(models.User.id==id).first()
    print(user)
    if not user:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND
        ,detail=f"user  with id:{id} does not exist")
    

    return user



            