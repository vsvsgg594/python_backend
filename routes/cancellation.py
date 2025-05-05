from  fastapi import APIRouter,Depends
from database import db_dependency
from models import Cancellation
from base_model import cancellation,addPagination
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from routes.token import decode_token, bearer_scheme
router=APIRouter()
@router.post("/create-policy",tags=["Policy"])
def createpolicy(cn:cancellation,db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
            decoded_token = decode_token(token.credentials)
            if isinstance(decoded_token, JSONResponse):
                return decoded_token
            user_type = decoded_token.get('userType')
            userid=decoded_token.get("userId")
            if user_type != "admin":
                return JSONResponse(status_code=403, detail="You lack admin privileges")
            db_cancellation = Cancellation(userId=userid,policyname=cn.policyname)

            # Add to the session and commit
            db.add(db_cancellation)
            db.commit()
             # Optionally refresh to get updated fields

            return JSONResponse(status_code=200, content={"detail": "Policy  added successfully"})
    except Exception as e:
            print(e)
            return JSONResponse(status_code=400,content={"detail":"Unable to add Policy"})
@router.delete("/delete-policy/{cancellationId}",tags=["Policy"])
async def deletepolicy(cancellationId:int,db:db_dependency, token: str = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userId=decoded_token.get('userId')
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=404, content={"detail": "you lack admin privilages"})
    try:
        policy= db.query(Cancellation).filter(Cancellation.cancellationId ==cancellationId , Cancellation.status == 0)
        if policy is None:
            return JSONResponse(status_code=404, content={"detail": "policy not found"})
        policy.status = 1
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "policy successfully deleted"})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"detail": "Failed to delete policy"})
    
@router.post("/viewall-policy",tags=["Policy"])
def viewallfeedback(lm:addPagination,db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        limit = int(lm.limit) if lm.limit else 10
        page = int(lm.page) if lm.page else 1
        offset = limit * (page - 1)
        if user_type != "admin" and user_type != "customer" and user_type != "merchant" and user_type != "delivaryAgent":
            return JSONResponse(status_code=403,content={"detail":"You lack login privileges"})
        
        data= db.query(Cancellation).limit(limit).offset(offset).all()
        if data is not None:
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(data)})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400,content={"detail":[]})
@router.put("/edit-policy/{cancellationId}",tags=["Policy"])
def update_details(cancellationId:int,cn:cancellation, db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, detail="You lack admin privileges")
        db_details = db.query(Cancellation).filter(Cancellation.cancellationId==cancellationId ).first()
        if db_details is None:
            return JSONResponse(status_code=404,content={"detail":"policy not found not found"})
        if cn.policyname:
            db_details.policyname = cn.policyname 
        if cn.isactive !="":
            db_details.isactive = cn.isactive
        
        db.commit()
       
        return JSONResponse(status_code=200, content={"detail": "policy updated successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to update policy "})