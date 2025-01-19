
import time
from fastapi import Body, FastAPI
from psycopg2.extras import  RealDictCursor
import psycopg2
from .import models
from .database import engine,get_db
from .routers import post,user,auth
from .config import Setting


models.Base.metadata.create_all(bind=engine)


app=FastAPI()

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router) 













try:
     conn = psycopg2.connect(host='localhost', database='postgres',user="postgres", password='40284433',
     cursor_factory=RealDictCursor)
     cursor = conn.cursor()
     print("Database connected successfully")
except Exception as error:
    print("Connection to database failed") 
    print("Error:",error) 
    time.sleep(2)   



   

         






