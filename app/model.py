from .database import Base
from sqlalchemy import Boolean, Column, Float, Integer, String

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)  # Unique identifier
    title = Column(String, nullable=False)  # Post title
    content = Column(String, nullable=False)  # Post content
    published = Column(Boolean, default=True)  # Whether the post is published
    rating = Column(Float, nullable=True)  # Post rating (optional)
