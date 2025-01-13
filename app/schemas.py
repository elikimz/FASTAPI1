from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr



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


# user create

class UserCreate(BaseModel):
    email:EmailStr
    password:str
    username:str
    is_active:bool

    
    # USER RESPONSE

class UserResponse(BaseModel):
    id:int
    email:EmailStr  
    username:str
    is_active:bool
    created_at:datetime
    
    class config:
        orm_mode=True


# User LOGIN

class Userlogin(BaseModel):
    email:EmailStr
    password:str