from .database import Base
from sqlalchemy import TIMESTAMP, Boolean, Column, Float, Integer, String, text,ForeignKey

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)  # Unique identifier
    title = Column(String, nullable=False)  # Post title
    content = Column(String, nullable=False)  # Post content
    published = Column(Boolean, default=True)  # Whether the post is published
    rating = Column(Float, nullable=True)  # Post rating (optional)
    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))

    user_id=Column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=False)



class User(Base):
    __tablename__ ="users"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique ID for each user
    username = Column(String(50), unique=False, nullable=False)  # Username (unique)
    email = Column(String(120), unique=True, nullable=False)  # Email (unique)
    password = Column(String(128), nullable=False)  # Password (hashed)
    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))
    is_active = Column(Boolean, default=True)  # Indicates if the user is active
