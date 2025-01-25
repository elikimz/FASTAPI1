# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from .config import Setting

# setting = Setting()
# SQLALCHEMY_DATABASE_URL= f'postgresql://{setting.database_username}:' \
# f'{setting.database_password}@' \
# f'{setting.database_hostname}:'\
# f'{setting.database_port}/'\
# f'{setting.database_name}'

# engine=create_engine(SQLALCHEMY_DATABASE_URL)

# SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

# Base=declarative_base()

# def get_db():
#      db=SessionLocal()
#      try:
#           yield db
#      finally:
#           db.close()



from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get the DATABASE_URL from the environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the SQLAlchemy engine using the DATABASE_URL
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
