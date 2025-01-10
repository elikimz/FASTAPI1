from .database import Base
from sqlalchemy import TIMESTAMP, Boolean, Column, Float, Integer, String, text

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)  # Unique identifier
    title = Column(String, nullable=False)  # Post title
    content = Column(String, nullable=False)  # Post content
    published = Column(Boolean, default=True)  # Whether the post is published
    rating = Column(Float, nullable=True)  # Post rating (optional)
    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))
