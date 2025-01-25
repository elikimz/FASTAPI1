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

# Get database credentials from environment
database_hostname = os.getenv("database_hostname")
database_port = os.getenv("database_port")
database_username = os.getenv("database_username")
database_password = os.getenv("database_password")
database_name = os.getenv("database_name")

# Construct the SQLAlchemy DATABASE_URL
SQLALCHEMY_DATABASE_URL = f"postgresql://{database_username}:{database_password}@{database_hostname}:{database_port}/{database_name}"

# Check if the DATABASE_URL was constructed correctly
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL could not be constructed. Please check environment variables.")

# Create SQLAlchemy engine and session
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
