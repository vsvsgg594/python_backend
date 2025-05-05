from typing import Optional
from fastapi import APIRouter,Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from database import db_dependency
from base_model import managecity,addPagination
from routes.token import bearer_scheme,decode_token
from models import Managecities
router=APIRouter()
@router.post("/create-cities", tags=["Cities"])
def managecities(mg:managecity,db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, detail="You lack admin privileges")
        db_details = Managecities(**mg.model_dump())
        db.add(db_details)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "details added successfully"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": "Unabel to add details "})
    

@router.post("/viewall-cities",tags=["Cities"])
def viewallcities(lm:addPagination,db:db_dependency,token: str = Depends(bearer_scheme)):
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
        
        data= db.query(Managecities).limit(limit).offset(offset).all()
        if data is not None:
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(data)})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400,content={"detail":[]})
    

@router.get("/view-singlecity",tags=["Cities"])
def singlecities(id:int,db:db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token 
        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, detail="You lack admin privileges")
        managecities = db.query(Managecities).filter(Managecities.managecityId== id).first()
        if managecities  is not None:
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(managecities)})
    except Exception as e:
        print(str(e))
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": []})

@router.delete("/delete-city/{managecityId}",tags=["Cities"])
async def deletecities(managecityId:int,db:db_dependency, token: Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin" and userType != "merchant":
        return JSONResponse(status_code=404, content={"detail": "you lack privilages"})
    try:
        managecities= db.query(Managecities).filter(Managecities.managecityId ==managecityId).first()
        if managecities is None:
            return JSONResponse(status_code=404, content={"detail": "data not found"})
        return JSONResponse(status_code=200, content={"detail": "data successfully deleted"})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"detail": "Failed to delete city"})
# @router.put("/editcities/{managecityId}",tags=["Cities"])
# async def update_details(mg:managecities,managecityId:int,db:db_dependency,token: str = Depends(bearer_scheme)):
#     try:
#         decoded_token = decode_token(token.credentials)
#         if isinstance(decoded_token, JSONResponse):
#             return decoded_token
#         user_type = decoded_token.get('userType')
#         if user_type != "admin":
#             return JSONResponse(status_code=403, detail="You lack admin privileges")
#         db_details = db.query(Managecities).filter(Managecities.managecityId==managecityId).first()
#         if db_details is None:
#             return JSONResponse(status_code=404,content={"detail":"cities  not found not found"})
#         if mg.name !="":
#             db_details.name = mg.name 
#         if mg.description !="":
#             db_details.description = mg.description
#         if mg.type !="":
#             db_details.type = mg.type 
#         if mg.isactive !="":
#             db_details.isactive = mg.isactive


@router.put("/edit-city/{managecityId}",tags=["Cities"])
async def update_details(mg:managecity,managecityId:int,db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, detail="You lack admin privileges")
        db_details = db.query(Managecities).filter(Managecities.managecityId==managecityId).first()
        if db_details is None:
            return JSONResponse(status_code=404,content={"detail":"cities  not found not found"})
        if mg.name !="":
            db_details.name = mg.name 
        if mg.description !="":
            db_details.description = mg.description
        if mg.type !="":
            db_details.type = mg.type 
        if mg.isactive !="":
            db_details.isactive = mg.isactive
        
        db.commit()
       
        return JSONResponse(status_code=200, content={"detail": "cities updated successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to update cities "})