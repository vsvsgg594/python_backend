from datetime import datetime
from typing import Optional
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from base_model import Discount, addPagination, editdiscount, assigndiscountmodel
import models
from fastapi import APIRouter, Depends
from database import db_dependency
from routes.token import decode_token, bearer_scheme

router=APIRouter()
#create 
@router.post("/add-discount",tags=["Discount"])
async  def creatediscount(ad:Discount,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        userType = decoded_token.get('userType')
        if userType != "admin":
            return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"}) 
        db_discount=models.discountTable(discountType = ad.discountType, discountName = ad.discountName, minimumOrderAmount= ad.minimumOrderAmount,description= ad.description,validfrom= ad.validfrom,validto= ad.validto,maxiamt= ad.maxiamt, discountValue= ad.discountValue)

        db.add(db_discount)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "discount added successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to add discount "})
    
#read multiple item
@router.post("/view-discount",tags=["Discount"])
async def viewdiscount(p:addPagination,db:db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        userType = decoded_token.get('userType')
        if userType != "admin":
            return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
        
        limit = int(p.limit) if p.limit else 10
        page = int(p.page) if p.page else 1
        offset = limit * (page - 1)

        data=db.query(models.discountTable)
        total = data.count()
        data= data.offset(offset).limit(limit).all()
        if data is not None:
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(data),"count":total})
        else:
            return JSONResponse(status_code=200,content={"detail":[]})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400,content={"detail":[]})
    

# #retrive a single item
# @router.get("/singlediscount/{discount_id}",tags=["Discount"])
# async def singlediscount(discount_id:int,db:db_dependency,token: Optional[str] = Depends(bearer_scheme)):
#     decoded_token = decode_token(token.credentials)
#     if isinstance(decoded_token, JSONResponse):
#         return decoded_token
#     userType = decoded_token.get('userType')
#     if userType != "admin" and userType != "deliveryagent":
#         return JSONResponse(status_code=404, content={"detail": "you lack privilages"})
#     try:
#         discount=db.query(models.discountTable).filter(models.discountTable.discountId==discount_id).first()
#         if discount is None:
#             return JSONResponse(status_code=404,content={"detail":"incentive not found"})    
#         db.delete(discount)
#         db.commit()
#         return JSONResponse(status_code=200, content={"detail": "incentive deleted"})
#     except Exception as e:
#         print(e)
#         db.rollback()
#         return JSONResponse(status_code=400, content={"detail":"unable to de incentive schedule"})

#retrive edit
@router.post("/edit-discount/{discount_id}",tags=["Discount"]) 
async def editdiscount(ed:editdiscount,discount_id:int,db:db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, detail="You lack admin privileges")
        db_discount=db.query(models.discountTable).filter(models.discountTable.discountId == discount_id).first()
        if db_discount is None:
            return JSONResponse(status_code=404, detail="discount not found")
        
        if ed.discountType !="":
            db_discount.discountType = ed.discountType
        
        if ed.discountName !="":
            db_discount.discountName = ed.discountName

        if ed.minimumOrderAmount !="":
            db_discount.minimumOrderAmount = ed.minimumOrderAmount
        
        if ed.description !="":
            db_discount.description = ed.description

        if ed.discountValue !="":
            db_discount.discountValue = ed.discountValue
        
        if ed.validfrom !="":
            newTime =  datetime.strptime(ed.validfrom,  "%Y-%m-%d %H:%M:%S.%f").date()
            db_discount.validfrom = newTime
            print(newTime)
        if ed.validto !="":
            db_discount.validto = datetime.strptime(ed.validto,  "%Y-%m-%d %H:%M:%S.%f")
        if ed.maxiamt !="":
            db_discount.maxiamt = ed.maxiamt
        
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "discount  updated successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail":"unable to update discount schedule"})
#delete
@router.delete("/delete-discount/{discount_id}",tags=["Discount"])
async def deletediscount(db:db_dependency,discount_id:int,token: Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=404, content={"detail": "you lack privilages"})
    try:
        db_discount=db.query(models.discountTable).filter(models.discountTable.discountId==discount_id).first()
        if db_discount is None:
            return JSONResponse(status_code=404, detail="discount not found")
        
        db_discount.status = 0
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "discount deleted"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail":"unable to add discount "})


@router.post("/assign-discount",tags=["Discount"]) 
async def assigndiscount(ed:assigndiscountmodel,db:db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, detail="You lack admin privileges")
        
        for merchant in ed.merchantId:

            addtodb = models.discountMerchantTable(discountId= ed.discountId, merchantId = merchant)
            deleteExisting = db.query(models.discountMerchantTable).filter(models.discountMerchantTable.merchantId == merchant).first()
            if deleteExisting is not None:
                db.delete(deleteExisting)
            db.add(addtodb)

        db.commit()
        return JSONResponse(status_code=200, content={"detail":"discount assigned"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail":"unable to assign discount"})