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
from .config import Setting

# Load settings from environment variables or config
setting = Setting()

# Corrected SQLALCHEMY_DATABASE_URL with SSL and Endpoint Options
SQLALCHEMY_DATABASE_URL = (
    f'postgresql+psycopg2://{setting.database_username}:'
    f'{setting.database_password}@'
    f'{setting.database_hostname}:'
    f'{setting.database_port}/'
    f'{setting.database_name}'
    f'?sslmode=require&options=endpoint%3Dep-muddy-river-a8h4r8vn'
)

# Create the SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Configure session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for getting DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
