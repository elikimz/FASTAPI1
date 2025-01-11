
from app import models,schemas,utils
from fastapi import Body,HTTPException,status,Depends,APIRouter
from sqlalchemy.orm import Session
from ..database import get_db

router=APIRouter(
     prefix="/users"
)

@router.post("/",status_code=status.HTTP_201_CREATED,response_model=schemas.UserResponse)
def create_user(new_user:schemas.UserCreate, db:Session = Depends(get_db)):
     
     hashed_password=utils.hash(new_user.password)
     new_user.password=hashed_password
     new_user= models.User(
       **new_user.dict()
    )
     db.add(new_user) 
     db.commit()
     db.refresh(new_user)
   
     return new_user
   



@router.get('/{id}',response_model=schemas.UserResponse)
def get_user(id:int,db:Session = Depends(get_db)):
    user=db.query(models.User).filter(models.User.id==id).first()
    print(user)
    if not user:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND
        ,detail=f"user  with id:{id} does not exist")
    

    return user





            