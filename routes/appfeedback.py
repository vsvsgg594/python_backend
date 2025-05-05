from  fastapi import APIRouter,Depends
from database import db_dependency
from models import AppFeedback
from base_model import feedback,addPagination
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from routes.token import decode_token, bearer_scheme
router=APIRouter()
@router.post("/appfeedback",tags=["AppFeedback"])
def appfeedback(fs:feedback,db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        userid=decoded_token.get("userId")
        if user_type != "customer":
            return JSONResponse(status_code=403, detail="You lack customer privileges")
        db_appfeedback = AppFeedback(userId=userid,appfeedback=fs.feedback)

        # Add to the session and commit
        db.add(db_appfeedback)
        db.commit()
        db.refresh(db_appfeedback)  # Optionally refresh to get updated fields

        return JSONResponse(status_code=200, content={"detail": "Appfeedback added successfully"})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=400,content={"detail":"Unable to Appfeedback"})

@router.post("/viewall-appfeedback",tags=["AppFeedback"])
def viewallfeedback(lm:addPagination,db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        limit = int(lm.limit) if lm.limit else 10
        page = int(lm.page) if lm.page else 1
        offset = limit * (page - 1)
        if user_type != "admin":
            return JSONResponse(status_code=403,content={"detail":"You lack admin privileges"})
        
        data= db.query(AppFeedback).limit(limit).offset(offset).all()
        if data is not None:
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(data)})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400,content={"detail":[]})
    
    