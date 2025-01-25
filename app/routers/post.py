from fastapi import Body, HTTPException, status, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from . import oauth2
from sqlalchemy import func
router = APIRouter(tags=["POSTS"])

@router.get("/", tags=["DEFAULT"])
def root():
    return {"message": "Welcome to my FASTAPI"}

@router.get("/posts")
def get_posts(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    posts = db.query(models.Post).all()

    # Collect the posts and their vote counts
    results = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id == models.Post.id, isouter=True
    ).group_by(models.Post.id).all()

    # Create a response structure that can be serialized
    return [
        {"post": post, "votes": votes} 
        for post, votes in results
    ]


@router.get("/posts/{id}")
def get_post_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    post = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id == models.Post.id, isouter=True
    ).group_by(models.Post.id).filter(models.Post.id == id).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {id} does not exist",
        )
    
    # post[0] is the Post object, and post[1] is the vote count
    post_data = post[0].__dict__  # Convert Post model to a dictionary
    post_data["votes"] = post[1]  # Add the vote count to the dictionary

    return post_data

@router.post("/posts", response_model=schemas.Post, status_code=201)
def create_post(
    new_post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user:int = Depends(oauth2.get_current_user)
       
):
    print(f"Current user: {current_user}")  # Debug current_user
    print(f"Current user ID: {current_user.id}")

   
    post = models.Post(**new_post.dict(),user_id=current_user.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

@router.delete("/posts/{id}", status_code=204)
def delete_post(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    
    post=post_query.first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {id} does not exist",
    
        )
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,detail="Not authorisedg to perform requested action"
        )


    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}

@router.put("/posts/{id}", response_model=schemas.Post)
def update_post(
    id: int,
    post: schemas.PostUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    query = db.query(models.Post).filter(models.Post.id == id)
    existing_post = query.first()
    if not existing_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {id} does not exist",
        )
    if existing_post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,detail="Not authorised to perform requested action"
        )

    query.update(post.dict(), synchronize_session=False)
    db.commit()
    db.refresh(existing_post)
    return existing_post
