from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from database import db_dependency
from routes.token import bearer_scheme,decode_token
from models import deliverysettingTable
from base_model import deliverysettings
router=APIRouter()


@router.get("/viewall-deliverysettings",tags=["DeliverySetting"])
async def viewallprefernce(db:db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
       
    
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"detail":"You lack admin privileges" })
        # Query to join the User and ManagerTable
        deliverysettings = db.query(deliverysettingTable).first()
        if deliverysettings is None:
           return JSONResponse(status_code=200, content={"detail":[]})
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(deliverysettings)})
    except Exception as e:
        # Log the exception for debugging
        print(e)  # Replace with your logging mechanism
        return JSONResponse(status_code=400,content={"detail":"Unable to deliverysettings details"})

@router.put("/edit-deliverysettings/{deliverysettingId}", tags=["DeliverySetting"])
async def edit_manager(deliverysettingId: int,ds:deliverysettings, db: db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
       
    
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
        # Retrieve the manager and associated user
        preference = db.query( deliverysettingTable).filter(deliverysettingTable.deliverysettingId == deliverysettingId).first()
        if preference is None:
            return JSONResponse(status_code=404,content={"detail":"preference  not found"})
        # Update the manager details
        
        
        if ds.deliveryTime !="":
          preference.deliveryTime = ds.deliveryTime
        
        
        if ds.chargePerKm !="":
          preference.chargePerKm = ds.chargePerKm
              
        
        if ds.freeDelivery !="":
          preference.freeDelivery = ds.freeDelivery
        
        
        if ds.defaultDeliveryManager !="":
          preference.defaultDeliveryManager = ds.defaultDeliveryManager
        
        if ds.externaldeliveryCharge !="":
          preference.externaldeliveryCharge = ds.externaldeliveryCharge
          
        if ds.deliveryCharge !="":
          preference.deliveryCharge = ds.deliveryCharge
          
        if ds.merchantWiseDeliveryCharge !="":
          preference.merchantWiseDeliveryCharge = ds.merchantWiseDeliveryCharge    
          
        if ds.staticsAddress !="":
          preference.staticsAddress = ds.staticsAddress  
           
        if ds.tip !="":
          preference.tip = ds.tip  
          
        db.commit()

        return JSONResponse(status_code=200,content={"detail": "Manager and user details updated successfully"})

    except Exception as e:
        # Log the exception for debugging
        print(e)  # Replace with your logging mechanism
        return JSONResponse(status_code=400,content={"detail":"Unable to update manager"})
