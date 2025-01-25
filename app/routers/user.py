
from app import models,schemas,utils
from fastapi import Body,HTTPException,status,Depends,APIRouter
from sqlalchemy.orm import Session
from ..database import get_db

router=APIRouter(
     prefix="/users",
     tags=['USERS']
)

@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
def create_user(new_user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if the user already exists
    existing_user = db.query(models.User).filter(models.User.email == new_user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    # Hash the password
    hashed_password = utils.hash(new_user.password)
    new_user.password = hashed_password
    
    # Create and save the new user
    new_user_record = models.User(**new_user.dict())
    db.add(new_user_record)
    db.commit()
    db.refresh(new_user_record)

    return new_user_record



@router.get('/{id}',response_model=schemas.UserResponse)
def get_user(id:int,db:Session = Depends(get_db)):
    user=db.query(models.User).filter(models.User.id==id).first()
    print(user)
    if not user:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND
        ,detail=f"user  with id:{id} does not exist")
    

    return user





            