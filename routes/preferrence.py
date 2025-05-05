from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from database import db_dependency
from routes.token import bearer_scheme,decode_token
from models import PreferenceTable
from base_model import prefernce
router=APIRouter()

# @router.get("/viewallpreference",tags=["Preference"])
@router.get("/viewall-preference",tags=["Preference"])
async def viewallprefernce(db:db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
       
    
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"detail":"You lack admin privileges" })
        # Query to join the User and ManagerTable
        preference = db.query(PreferenceTable).first()
        if preference is None:
           return JSONResponse(status_code=200, content={"detail": []})
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(preference)})
    except Exception as e:
        # Log the exception for debugging
        print(e)  # Replace with your logging mechanism
        return JSONResponse(status_code=400,content={"detail":"Unable to retrieve preference"})

@router.put("/edit-preference/{preferenceId}", tags=["Prefernce"])
async def edit_preference(preferenceId: int,pf:prefernce, db: db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
       
    
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
        # Retrieve the manager and associated user
        preference = db.query(PreferenceTable).filter(PreferenceTable.preferenceId == preferenceId).first()
        if preference is None:
            return JSONResponse(status_code=404,content={"detail":"preference  not found"})
        # Update the manager details
        
        if pf.countryCode !="":
           preference.countryCode = pf.countryCode
           
        if pf.currency !="":
           preference.currency = pf.currency
           
        if pf.currencyFormatting !="":
           preference.currencyFormatting = pf.currencyFormatting
           
        if pf.timeZone !="":
           preference.timeZone = pf.timeZone
           
        if pf.timeFormat !="":
           preference.timeFormat = pf.timeFormat
           
        if pf.dateFormat !="":
           preference.dateFormat = pf.dateFormat
           
        if pf.onlineAndOfflineTax !="":
           preference.onlineAndOfflineTax = pf.onlineAndOfflineTax
           
        if pf.productShare !="":
           preference.productShare = pf.productShare
           
        if pf.shortenAddressOnMap !="":
           preference.shortenAddressOnMap = pf.shortenAddressOnMap
           
        if pf.productShare !="":
           preference.productShare = pf.productShare
           
        if pf.deliveryAddressConfirmation !="":
           preference.deliveryAddressConfirmation = pf.deliveryAddressConfirmation
           
        if pf.aerialDistance !="":
           preference.aerialDistance = pf.aerialDistance
           
        if pf.productShare !="":
           preference.favoriteMerchants = pf.favoriteMerchants
           
        if pf.autoRefund !="":
           preference.autoRefund = pf.autoRefund
           
        if pf.pickupNotifications !="":
           preference.pickupNotifications = pf.pickupNotifications
           
        if pf. orderReadyStatus!="":
           preference.orderReadyStatus = pf.orderReadyStatus
           
        if pf.distanceUnit !="":
           preference.distanceUnit = pf.distanceUnit
           
        if pf.showCommisionToMerchants !="":
           preference.showCommisionToMerchants = pf.showCommisionToMerchants
           
        if pf.customerRating !="":
           preference.customerRating = pf.customerRating
           
        if pf.hideCustomerDetailFromMerchant !="":
           preference.hideCustomerDetailFromMerchant = pf.hideCustomerDetailFromMerchant
           
        if pf.showCustomerProfileToMerchant !="":
           preference.showCustomerProfileToMerchant = pf.showCustomerProfileToMerchant
           
        if pf.showCurrencyToMerchant !="":
           preference.showCurrencyToMerchant = pf.showCurrencyToMerchant
           
        if pf.showGeofenceToMerchant !="":
           preference.showGeofenceToMerchant = pf.showGeofenceToMerchant
           
        if pf.showacceptOrrejectmerchants !="":
           preference.showacceptOrrejectmerchants = pf.showacceptOrrejectmerchants
       
        db.commit()

        return JSONResponse(status_code=200,content={"detail": "Manager and user details updated successfully"})

    except Exception as e:
        # Log the exception for debugging
        print(e)  # Replace with your logging mechanism
        return JSONResponse(status_code=400,content={"detail":"Unable to update manager"})
