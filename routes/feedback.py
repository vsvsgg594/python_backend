from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from database import db_dependency
from models import Feedback
from base_model import feedback,addPagination
from routes.token import decode_token, bearer_scheme
router=APIRouter()

@router.post("/create-feedback",tags=["Feedback"])
def createfeedback(fd:feedback,db:db_dependency, token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        user_id=decoded_token.get('userId')
        
        if user_type != "customer":
            return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
        db_feedback =Feedback(userid=user_id,**fd.model_dump())
        db.add(db_feedback)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "feedback added successfully"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": " Unabel to add feedback"})

# @router.post("/editfeedback",tags=["Feedback"])
# def editfeedback(fd:feedback,id:int,db: db_dependency, token: Optional[str] = Depends(bearer_scheme)):
#     try:
#         decoded_token = decode_token(token.credentials)
#         user_type = decoded_token.get('userType')
#         if user_type != "admin":
#             return JSONResponse(status_code=403, detail="You lack admin privileges")
#         db_feedback= db.query(Feedback).filter(Feedback.id == id).first()
#         if db_feedback is None:
#             return JSONResponse(status_code=404, content={"detail":"feedback not found"})
#         for key, value in fd.model_dump().items():
#             setattr(db_feedback, key, value)

#         db.commit()

#         return JSONResponse(status_code=200, content={"detail": "feedback  updated successfully"})
#     except Exception as e:
#         db.rollback()
#         print(e)
#         return JSONResponse(status_code=500,content={ "detail":"Failed to update feedback"})
    
# @router.get("/viewsinglefeedback",tags=["Feedback"])
# def singlefeedback(id:int,db:db_dependency,token: Optional[str] = Depends(bearer_scheme)):
#     try:
#         decoded_token = decode_token(token.credentials)
#         if isinstance(decoded_token, JSONResponse):
#             return decoded_token 
#         user_type = decoded_token.get('userType')
#         if user_type != "admin":
#             return JSONResponse(status_code=403, detail="You lack admin privileges")
#         feedback = db.query(Feedback).filter(Feedback.id == id).first()
#         if feedback is not None:
#             return JSONResponse(status_code=200, content={"detail": jsonable_encoder(feedback)})
#     except Exception as e:
#         print(str(e))
#         db.rollback()
#         return JSONResponse(status_code=400, content={"detail": []})


@router.post("/viewall-feedback",tags=["Feedback"])
def viewallfeedback(lm:addPagination,db:db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        limit = int(lm.limit) if lm.limit else 10
        page = int(lm.page) if lm.page else 1
        offset = limit * (page - 1)
        if user_type != "admin":
            return JSONResponse(status_code=403, detail="You lack admin privileges")
        
        data= db.query(Feedback)
        count = data.count()
        data = data.limit(limit).offset(offset).all()
        if data is not None:
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(data),"count":count})
        return JSONResponse(status_code=200,content={"detail":[],"count":0})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400,content={"detail":[]})
            