from fastapi import APIRouter,Depends
from database import db_dependency
from routes.token import decode_token, bearer_scheme
from typing import Optional
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from base_model import loyalityModel
from models import *

router=APIRouter()

def to_float_dict(self):
    return {
        'earningCriteriaAmount': float(self.earningCriteriaAmount),
        'earningCriteriaPoint': float(self.earningCriteriaPoint),
        'minimumOrderAmount': float(self.minimumOrderAmount),
        'maximumEarningPoint': float(self.maximumEarningPoint),
        'expiryDuration': float(self.expiryDuration),
        'redemptionPoint': float(self.redemptionPoint),
        'redemptionAmount': float(self.redemptionAmount),
        'redemptionOrderAmount': float(self.redemptionOrderAmount),
        'minimumLoyalityPointForRedemption': float(self.minimumLoyalityPointForRedemption),
    }

@router.post("/add-loyality", tags=['Loyality'])
async def addLoyality(lm:loyalityModel,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    try:
        floatvalues = lm.to_float_dict()
        addloyal = Loyality(**floatvalues)
        db.add(addloyal)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "loyality criterion added"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to add loyality"})
    

@router.post("/edit-loyality", tags=['Loyality'])
async def editLoyality(lm:loyalityModel,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    try:
        fetch = db.query(Loyality).first()

        if lm.earningCriteriaAmount != "":
            fetch.earningCriteriaAmount = float(lm.earningCriteriaAmount)
        if lm.earningCriteriaPoint != "":
            fetch.earningCriteriaPoint = float(lm.earningCriteriaPoint)
        if lm.maximumEarningPoint != "":
            fetch.maximumEarningPoint = float(lm.maximumEarningPoint)
        if lm.minimumLoyalityPointForRedemption != "":
            fetch.minimumLoyalityPointForRedemption = float(lm.minimumLoyalityPointForRedemption)
        if lm.minimumOrderAmount != "":
            fetch.minimumOrderAmount = float(lm.minimumOrderAmount)
        if lm.redemptionAmount != "":
            fetch.redemptionAmount = float(lm.redemptionAmount)
        if lm.redemptionOrderAmount != "":
            fetch.redemptionOrderAmount = float(lm.redemptionOrderAmount)
        if lm.redemptionPoint != "":
            fetch.redemptionPoint = float(lm.redemptionPoint)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "loyality criterion updated"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to update loyality"})
    
@router.get("/view-loyality", tags=['Loyality'])
async def viewLoyality(db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    # userType = decoded_token.get('userType')
    # if userType != "admin":
    #     return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    try:
        fetch = db.query(Loyality).first()

        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(fetch)})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to add loyality"})