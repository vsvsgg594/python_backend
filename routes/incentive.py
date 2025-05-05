from fastapi import APIRouter,Depends
from fastapi.encoders import jsonable_encoder
from base_model import incentive,addPagination
from database import db_dependency
from routes.token import decode_token,bearer_scheme
from fastapi.responses import JSONResponse
from models import incentiveStructureModel

router=APIRouter()
@router.post("/create-incentive", tags=["Incentive"])
async def create_incentive(ns: incentive, db: db_dependency, token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"message": "You lack admin privileges"})
        # existing_incentive = db.query(incentiveStructureModel).filter_by(type=ns.type).first()
        # if existing_incentive:
        #     return JSONResponse(status_code=400, content={"message": "An incentive of this type already exists"})
        db_incentive = incentiveStructureModel(earning=ns.earning, amountLimit=ns.amountlimit,type=ns.type)
        db.add(db_incentive)
        db.commit()
        
        return JSONResponse(status_code=200, content={"message": "Incentive added successfully"})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=400, content={"message": "Unable to add incentive"})
    
@router.post("/edit-incentive/{incentiveid}",tags=["Incentive"])
async def editincentive(incentiveid:int,ns:incentive,db:db_dependency,token:str=Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=404, content={"detail": "you lack privilages"})
    try:
        incentive = db.query(incentiveStructureModel).filter(incentiveStructureModel.incentiveId== incentiveid).first()
        if incentive is None:
            return JSONResponse(status_code=404,content={"detail":"incentive not found"})
        if ns.earning != "":
            incentive.earning = float(ns.earning)
        if ns.amountlimit != "":
            incentive.amountLimit = float(ns.amountlimit)
        if ns.type != "":
            incentive.type = float(ns.type)
        db.commit()
       
        return JSONResponse(status_code=200, content={"detail": "incentive  updated successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail":"unable to update incentive schedule"})
        
@router.delete("/delete-incentive/{incentiveid}",tags=["Incentive"])
async def delete_incentives(incentiveid:int, db:db_dependency,token: str = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=404, content={"detail": "you lack privilages"})
    try:
        db_incentive= db.query(incentiveStructureModel).filter(incentiveStructureModel.incentiveId ==incentiveid).first()
        if db_incentive is None:
            return JSONResponse(status_code=404,content={"detail":"incentive not found"})
            
        db.delete(db_incentive)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "incentive deleted"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail":"unable to de incentive schedule"})


@router.get("/view-incentive", tags=["Incentive"])
async def viewIncentive(db: db_dependency, token: str = Depends(bearer_scheme)):
    
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    user_type = decoded_token.get('userType')
    if user_type != "admin" and user_type != "deliveryAgent":
        return JSONResponse(status_code=403, content={"message": "You lack admin privileges"})

    try:    
        fetch = db.query(incentiveStructureModel).order_by(incentiveStructureModel.type).all()
        if fetch is None:
            return JSONResponse(status_code=200, content={"detail": []})
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(fetch)})

    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail":[]})



            