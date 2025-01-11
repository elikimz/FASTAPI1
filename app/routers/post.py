
from fastapi import Body,HTTPException,status,Depends,APIRouter
from sqlalchemy.orm import Session
from ..import models,schemas
from ..database import get_db

router=APIRouter(
    prefix="/posts"
)

# @router.get("/")
# def root():
#     return {"message": "Welcome to my FASTAPI"}



@router.get("/",response_model=list[schemas.Post])
def get_posts(db:Session = Depends(get_db)):
    
    posts=db.query(models.Post).all()
    return posts



@router.get("/{id}")
def get_posts(id: int,db:Session = Depends(get_db)):
   test_post= db.query(models.Post).filter(models.Post.id== id).first()
   print(test_post)

   if not test_post:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND
        ,detail=f"post with id:{id} does not exist")

   return  test_post 
       
    # Return the fetched row directly

 


@router.post("/",response_model=schemas.Post)
def create_posts(new_post:schemas.PostCreate,db:Session = Depends(get_db)):
  new_posts= models.Post(
       **new_post.dict()
  )
  db.add(new_posts) 
  db.commit()
  db.refresh(new_posts)
   
  return new_posts



   

@router.delete("/{id}")
def delete_posts(id:int,db:Session = Depends(get_db)):
    
    deleted_post=db.query(models.Post).filter(models.Post.id== id).first()
    
    if not deleted_post:
             
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND
        ,detail=f"post with id:{id} does not exist")
    db.delete(deleted_post)
    db.commit()

    return "post deleted successifully"

   


@router.put("/{id}")
def update_posts(id:int,post:schemas.PostUpdate,db:Session = Depends(get_db)):

    updated_query=db.query(models.Post).filter(models.Post.id == id)
    existing_post =updated_query.first()


  
    if not existing_post:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND
        ,detail=f"post with id:{id} does not exist")
    
    
    updated_query.update(post.dict(),synchronize_session=False)

    db.commit()
    db.refresh(existing_post)
    return    existing_post
