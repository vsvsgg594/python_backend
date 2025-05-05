from fastapi import APIRouter, Depends
from typing import Optional
from models import loginTypesModel, orderSettingsModel
from database import db_dependency
from fastapi.responses import JSONResponse
from routes.token import decode_token, bearer_scheme
from base_model import loginTypeBase, orderSettingBase
from fastapi.encoders import jsonable_encoder



router = APIRouter()

@router.post("/view-logintypes", tags=["loginTypes"])
async def viewLoginTypes(db:db_dependency):

    try:

        fetch = db.query(loginTypesModel).first()
        if fetch is None:
            return JSONResponse(status_code=200, content={"detail": []})
        
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(fetch)})

   
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": []})


@router.put("/edit-logintypes", tags=["loginTypes"])
async def editLoginTypes(db:db_dependency, lb:loginTypeBase, token:Optional[str] = Depends(bearer_scheme)):

    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    try:
        fetch = db.query(loginTypesModel).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail": "not found"})
        
        if lb.google != "":
            fetch.google = lb.google
        if lb.facebook != "":
            fetch.facebook = lb.facebook
        if lb.whatsapp != "":
            fetch.whatsapp = lb.whatsapp
        if lb.otp != "":
            fetch.otp = lb.otp
        if lb.signupUsingEmail != "":
            fetch.signupUsingEmail = lb.signupUsingEmail
        if lb.signupUsingPhone != "":
            fetch.signupUsingPhone = lb.signupUsingPhone
        if lb.emailVerification != "":
            fetch.emailVerification = lb.emailVerification
        if lb.otp != "":
            fetch.otp = lb.otp

        db.commit()
        return JSONResponse(status_code=200, content={"detail": "successfully updated"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to edit"})
    


@router.put("/edit-ordersettings", tags=["orderSettings"])
async def editOrderSettings(db:db_dependency, ob:orderSettingBase, token:Optional[str] = Depends(bearer_scheme)):

    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    try:
        fetch = db.query(orderSettingsModel).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail": "not found"})
        
        if ob.allowCustomersToRate != "":
            fetch.allowCustomersToRate = ob.allowCustomersToRate
        if ob.allowManagerToEdit != "":
            fetch.allowManagerToEdit = ob.allowManagerToEdit
        if ob.allowMerchantToEdit != "":
            fetch.allowMerchantToEdit = ob.allowMerchantToEdit
        if ob.autoAccept != "":
            fetch.autoAccept = ob.autoAccept
        if ob.orderAcceptanceTime != "":
            fetch.orderAcceptanceTime = ob.orderAcceptanceTime

        db.commit()
        return JSONResponse(status_code=200, content={"detail": "successfully updated"})
        
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to edit"})
    

@router.post("/view-ordersettings", tags=["orderSettings"])
async def viewOrderSettings(db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):

    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})

    try:

        fetch = db.query(orderSettingsModel).first()
        if fetch is None:
            return JSONResponse(status_code=200, content={"detail": []})
        
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(fetch)})

   
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": []})