from datetime import datetime
from typing import Optional
from pydantic import BaseModel



class PostBase(BaseModel):
    title:str
    content:str
    published:bool=True
    rating:Optional[int]=None 

class PostCreate(PostBase):
    pass    

class PostUpdate(PostBase):
    pass


# post response

class Post(BaseModel):
    title:str
    content:str
    published:bool
    rating:Optional[int]=None 
    created_at:datetime
    updated_at:datetime

    class config:
        orm_mode=True