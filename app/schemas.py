from datetime import datetime
from typing import Optional,Union
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
    user_id:int

    class Config:
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

class UserLogin(BaseModel):
    email:EmailStr
    password:str

    # TOKEN

class Token(BaseModel):
        access_token:str
        token_type:str

        
        # token response
class TokenData(BaseModel):
        id:Optional[Union[str,int]]=None