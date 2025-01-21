from fastapi import Body, HTTPException, status, Depends, APIRouter
from .. import schemas,database,models
from . import oauth2
from sqlalchemy.orm import Session

router=APIRouter(
    prefix="/vote"
    tags=['vote']
)

@router.post("/",status_code=status.HTTP_201_CREATED)
def vote(vote:schemas.Vote,db:Session=Depends(database.get_db),current_user:int =Depends(oauth2.get_current_user)):
    if (vote.dir==1):
        db.query(models.Vote).filter(models.Vote.post_id==vote.post_id)
     