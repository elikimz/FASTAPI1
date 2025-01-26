
import time
from fastapi import Body, FastAPI
from psycopg2.extras import  RealDictCursor
import psycopg2
from .import models
from .database import engine,get_db
from .routers import post,user,auth,vote
from .config import Setting
from fastapi.middleware.cors import CORSMiddleware


# models.Base.metadata.create_all(bind=engine)


app=FastAPI()

origins =[
         "*"
      ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router) 
app.include_router(vote.router)













# try:
#      conn = psycopg2.connect(host='localhost', database='postgres',user="postgres", password='40284433',
#      cursor_factory=RealDictCursor)
#      cursor = conn.cursor()
#      print("Database connected successfully")
# except Exception as error:
#     print("Connection to database failed") 
#     print("Error:",error) 
#     time.sleep(2)   


# Database connection for testing
try:
    # Use the connection string from Render
    conn = psycopg2.connect(
        host='dpg-cuaugobqf0us73cbeu20-a',  # Correct Render-hosted PostgreSQL database hostname
        database='database_fastapi',  # The database name you created
        user='database_fastapi_user',  # The database user you created
        password='2RU6nNNBZxa2lP8jiuhYMCOihUOklF8U',  # The password you created
        cursor_factory=RealDictCursor
    )
    cursor = conn.cursor()
    print("Database connected successfully")
except Exception as error:
    print("Connection to database failed")
    print("Error:", error)
    time.sleep(2)

         






