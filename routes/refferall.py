from fastapi import APIRouter, Depends
from typing import Optional
from models import referralModel
from database import db_dependency
from routes.token import decode_token, bearer_scheme
from fastapi.responses import JSONResponse
from base_model import referbase

router = APIRouter(tags=["referral"])


@router.post("/edit-referral/{referId}")
async def editReferral(referId:int,rb:referbase, db:db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    user_type = decoded_token.get('userType')
    
    if user_type != "admin":
        return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
    try:
        fetch = db.query(referralModel).filter(referralModel.referId == referId).first()


        if rb.referralType != "":
            fetch.referralType = int(rb.referralType)
        if rb.pointsPerReferal != "":
            fetch.pointsPerReferal = float(rb.pointsPerReferal)
        if rb.referrerDescription != "":
            fetch.referrerDescription = rb.referrerDescription
        if rb.refereeDiscountPercentange != "":
            fetch.refereeDiscountPercentange = float(rb.refereeDiscountPercentange)
        if rb.refereeMaximumDiscountValue != "":
            fetch.refereeMaximumDiscountValue = float(rb.refereeMaximumDiscountValue)
        
        if rb.minimumOrderAmount != "":
            fetch.minimumOrderAmount = float(rb.minimumOrderAmount)
        if rb.refereeDescription != "":
            fetch.refereeDescription = rb.refereeDescription
        if rb.minimumOrderAmountSwitch != "":
            fetch.minimumOrderAmountSwitch = int(rb.minimumOrderAmountSwitch)
        
        
        if rb.refereeDescriptionSwitch != "":
            fetch.refereeDescriptionSwitch = int(rb.refereeDescriptionSwitch)
        if rb.refereeMaximumDiscountValueSwitch != "":
            fetch.refereeMaximumDiscountValueSwitch = int(rb.refereeMaximumDiscountValueSwitch)

        return JSONResponse(status_code=200, content={"detail":"referral updated"})
    
    except Exception as e:
        # Log the exception for debugging
        print(e)  # Replace with your logging mechanism
        return JSONResponse(status_code=400,content={"detail":"unable to edit"})
    
    
        


@router.get("/view-referral")
async def viewReferral(db: db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    user_type = decoded_token.get('userType')
    
    if user_type != "admin" and user_type != "customer":
        return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
    
    try:
        fetch = db.query(referralModel).all()
        if fetch is None:
            return JSONResponse(status_code=200,content={"detail":[]})
        return JSONResponse(status_code=200,content={"detail":fetch})
    except Exception as e:
        # Log the exception for debugging
        print(e)  # Replace with your logging mechanism
        return JSONResponse(status_code=400,content={"detail":[]})