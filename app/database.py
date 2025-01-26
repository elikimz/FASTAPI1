from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import Setting

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
from .config import setting  # Import the settings instance

# Use the DATABASE_URL from environment variables for the Neon database connection
SQLALCHEMY_DATABASE_URL = setting.database_url

# Create the database engine using the constructed URL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a session maker bound to the engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# Dependency for getting the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
