from fastapi import APIRouter,Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from base_model import deliveryagentpersonaldata,addPagination
from database import db_dependency
from routes.token import decode_token,bearer_scheme
from models import deliveryAgentPersonalData

router=APIRouter()


@router.post("/create-deliveryagent-data",tags=["Deliveryagentdata"])
def createdeliveryagentdata(dp: deliveryagentpersonaldata,db:db_dependency,token: str=Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        userid=decoded_token.get('userId')
        if user_type != "deliveryAgent":
            return JSONResponse(status_code=403, content={"detail": "You lack admin privileges"})
        existing_detail = db.query(deliveryAgentPersonalData).filter(deliveryAgentPersonalData.userId == userid).first()
        if existing_detail:
            return JSONResponse(status_code=409, content={"detail": "Details already exist for this user."}) 
        existing_aadhar = db.query(deliveryAgentPersonalData).filter(deliveryAgentPersonalData.aadharCard == dp.aadharcard).first()
        if existing_aadhar:
            return JSONResponse(status_code=409, content={"detail": "Aadhar card number already exists."})

        existing_pan = db.query(deliveryAgentPersonalData).filter(deliveryAgentPersonalData.panCard == dp.pancard).first()
        if existing_pan:
            return JSONResponse(status_code=409, content={"detail": "PAN card number already exists."})
   
        detail=deliveryAgentPersonalData(userId=userid,vehicleType=dp.vehicletype,vehicleNumber=dp.vehiclenumber,aadharCard=dp.aadharcard ,panCard=dp.pancard)
        db.add(detail)
        db.commit()
        
        return JSONResponse(status_code=200, content={"detail": "Detail added successfully"})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=400, content={"detail": "Unable to add Detail"})
    
# @router.post("/viewdelivaryagentdetail",tags=["Deliveryagentdata"])
# def viewdelivaryagentdetail(ad:addPagination,db:db_dependency,token:str=Depends(bearer_scheme)):
#     try:
#         limit = int(ad.limit) if ad.limit else 10
#         page = int(ad.page) if ad.page else 1
#         offset = limit * (page - 1)
#         decoded_token = decode_token(token.credentials)
#         if isinstance(decoded_token, JSONResponse):
#             return decoded_token
#         user_type = decoded_token.get('userType')
#         if user_type != "deliveryAgent":
#             return JSONResponse(status_code=403, content={"detail": "You lack admin privileges"})
#         data= db.query(deliveryAgentPersonalData).offset(offset).limit(limit).all()
#         if data is not None:
#             return JSONResponse(status_code=200, content={"detail": jsonable_encoder(data)})
#     except Exception as e:
#         print(e)
#         db.rollback()
#         return JSONResponse(status_code=400,content={"detail":[]})
    
@router.post("/edit-delivaryagent-detail",tags=["Deliveryagentdata"])
def editDeliveryagent(dp:deliveryagentpersonaldata,db:db_dependency,token:str=Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "deliveryAgent" and userType != "admin":
        return JSONResponse(status_code=404, content={"detail": "you lack privilages"})
    if userType == "admin":
        userId = int(dp.userId)
    try:
        existing_aadhar = db.query(deliveryAgentPersonalData).filter(deliveryAgentPersonalData.aadharCard == dp.aadharcard,deliveryAgentPersonalData.userId != userId).first()
        if existing_aadhar:
            return JSONResponse(status_code=409, content={"detail": "Aadhar card number already exists."})

        existing_pan = db.query(deliveryAgentPersonalData).filter(deliveryAgentPersonalData.panCard == dp.pancard,deliveryAgentPersonalData.userId != userId).first()
        if existing_pan:
            return JSONResponse(status_code=409, content={"detail": "PAN card number already exists."})
   
        deliverydetails = db.query(deliveryAgentPersonalData).filter(deliveryAgentPersonalData.userId==userId).first()
        if deliverydetails is None:
            return JSONResponse(status_code=404,content={"detail":"details not found"})
        if dp.vehicletype  !="":
            deliverydetails.vehicleType =dp.vehicletype 
        if dp.vehiclenumber !="":
            deliverydetails.vehicleNumber = dp.vehiclenumber
        if dp.aadharcard !="":
            deliverydetails.aadharCard =dp.aadharcard
        if dp.pancard !="":
            deliverydetails. panCard =dp.pancard
        db.commit()
       
        return JSONResponse(status_code=200, content={"detail": "details  updated successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail":"unable to update details "})
        

# @router.delete("/deleteagentdetail/{agentid}",tags=["Deliveryagentdata"])
# def deletetimeslot(agentid:int, db:db_dependency,token:str=Depends(bearer_scheme)):
#     decoded_token = decode_token(token.credentials)
#     if isinstance(decoded_token, JSONResponse):
#         return decoded_token
#     userType = decoded_token.get('userType')
#     if userType != "deliveryAgent":
#         return JSONResponse(status_code=404, content={"detail": "you lack privilages"})
#     try:
#         slot = db.query(deliveryAgentPersonalData).filter(deliveryAgentPersonalData.deliveryAgentPID == agentid).first()
#         if slot is None:
#             return JSONResponse(status_code=404,content={"detail":"details not found"})
        
#         db.delete(slot)
#         db.commit()
#         return JSONResponse(status_code=200, content={"detail": "detail deleted"})
#     except Exception as e:
#         print(e)
#         db.rollback()
#         return JSONResponse(status_code=400, content={"detail":"unable to update details"})
        