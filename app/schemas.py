from datetime import datetime
from typing import Optional,Union
from pydantic import BaseModel, EmailStr, validator,Field, constr
from pydantic.types import conint




class PostBase(BaseModel):
    title:str
    content:str
    published:bool=True
    rating:Optional[int]=None 
 

class PostCreate(PostBase):
    pass    

class PostUpdate(PostBase):
    title:str
    content:str
    published:bool=True
    rating:Optional[int]=None 
  
class UserResponse(BaseModel):
    id:int
    email:EmailStr  
    username:str
    is_active:bool
    created_at:datetime
    
    class config:
        orm_mode=True  


# post response

class Post(BaseModel):
    title:str
    content:str
    published:bool
    rating:Optional[int]=None 
    created_at:datetime
    updated_at:datetime
    user_id:int
   

    
    owner:UserResponse
    class Config:
        orm_mode=True

class PostOut(BaseModel):
     post:Post
     votes:int
     class Config:
        orm_mode=True
     

# user create

class UserCreate(BaseModel):
    email:EmailStr
    password:str
    username:str
    is_active:bool

    
    # USER RESPONSE




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


# Vote model
class Vote(BaseModel):
    post_id: int
    dir: int

    @validator("dir")
    def validate_dir(cls, value):
        if value not in (0, 1):
            raise ValueError("dir must be 0 or 1")
        return value
    
   