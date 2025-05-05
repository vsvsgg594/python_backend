
import os
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from database import db_dependency
from sqlalchemy.orm import joinedload
from models import Banner,merchantTable
from base_model import BannerCreate,addbannerPagination,bannerEdit
from fastapi.encoders import jsonable_encoder
from datetime import datetime

from routes.token import decode_token,bearer_scheme
router=APIRouter()
bucketLink = os.getenv('bucketLink')
@router.post("/create-banner", summary="the merchant and admin can create banner the banner admin created will be directly visible in user home page merchant created banners will be visible in his page if admin approves it will be shown in user home", tags=["Banner"])
async def create(bn:BannerCreate,db: db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userId=decoded_token.get('userId')
    userType = decoded_token.get('userType')
    if userType != "admin" and userType != "merchant":
        return JSONResponse(status_code=404, content={"detail": "you lack privilages"})
    
    try:
        banner = Banner(merchantId=bn.merchantId,bannervalidity=bn.bannervalidity,bannername=bn.bannername,choosefile=int(bn.choosefile), addToHome=1)

        if userType == "merchant":
            getMerchant = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
            if getMerchant is None:
                return JSONResponse(status_code=404, content={"detail": "unable to retrieve merchant"})
            bn.merchantId = getMerchant
            banner = Banner(merchantId=bn.merchantId,bannervalidity=bn.bannervalidity,bannername=bn.bannername,choosefile=int(bn.choosefile))
        # Read the file contents
         
        db.add(banner)
        db.commit()
        
        return JSONResponse(status_code=200, content={"detail": "banner created successfully"})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"detail": "Failed to create banner"})
    

@router.post("/view-banner",tags=["Banner"])
async def viewbanner(lm:addbannerPagination,db:db_dependency, token: Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userId=decoded_token.get('userId')
    userType = decoded_token.get('userType')
    limit = int(lm.limit) if lm.limit else 10
    page = int(lm.page) if lm.page else 1
    offset = limit * (page - 1)

    if userType != "admin" and userType != "merchant":
        return JSONResponse(status_code=404, content={"detail": "you lack privilages"})
    
    try:
        currentTime = datetime.now()
        fetch = db.query(Banner).options(joinedload(Banner.bannergallery))
        if userType == "merchant":
            getMerchant = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
            if getMerchant is None:
                return JSONResponse(status_code=404, content={"detail": "unable to retrieve merchant"})
            fetch = fetch.filter(Banner.merchantId == getMerchant)

        if lm.isExpired != "":
            if lm.isExpired == "0":
                fetch = fetch.filter(Banner.bannervalidity < currentTime) #expired banners
            elif lm.isExpired == "1":
                fetch = fetch.filter(Banner.bannervalidity > currentTime) #active banners
            else:
                return JSONResponse(status_code=406, content={"detail": "invalid expiry type"})
            
        fetch = fetch.filter(Banner.status == 0).order_by(Banner.bannerid.desc())
        totalCount = fetch.count()
        fetch = fetch.limit(limit).offset(offset).all()
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(fetch), "totalCount":totalCount})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"detail": []})

# @router.get("/viewsinglebanner/{bannerId}",tags=["Banner"])
# async def viewsinglebanner(bannerId:int,db:db_dependency):
#     view=db.query(Banner).filter(Banner.bannerid==bannerId).first()
#     if view is None:
#         return JSONResponse(status_code=404,content={"detail":"banner not found"})
#     else:
#         return JSONResponse(status_code=200,content={"detail":"banner found  successfully"})


@router.put("/edit-banner/{bannerId}", tags=["Banner"])
async def edit_banner(bannerId: int,bn: bannerEdit,db: db_dependency, token: Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userId=decoded_token.get('userId')
    userType = decoded_token.get('userType')
    if userType != "admin" and userType != "merchant":
        return JSONResponse(status_code=404, content={"detail": "you lack privilages"})
    try:
        banner = db.query(Banner).filter(Banner.bannerid == bannerId)
        if userType == "merchant":
            getMerchant = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
            if getMerchant is None:
                return JSONResponse(status_code=404, content={"detail": "unable to retrieve merchant"})
            banner = banner.filter(Banner.merchantId == getMerchant, Banner.addToHome == 0)
       
        # Fetch the existing banner
        banner = banner.first()
        if banner is None:
            return JSONResponse(status_code=404,content={"detail":"Banner not found"})
        
        if userType == "admin":
            if bn.addToHome != "":
                banner.addToHome = bn.addToHome

        # Update only the fields provided in the request
        if bn.bannervalidity  != "":
            banner.bannervalidity = bn.bannervalidity
        if bn.bannername  != "":
            banner.bannername = bn.bannername
        if bn.choosefile  != "":
            banner.choosefile = int(bn.choosefile)

        db.commit()
        
        return JSONResponse(status_code=200, content={"detail": "Banner updated successfully"})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"detail": "Failed to update banner"})


@router.delete("/delete-banner/{bannerId}",tags=["Banner"])
async def deletebanner(bannerId:int,db:db_dependency, token: Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userId=decoded_token.get('userId')
    userType = decoded_token.get('userType')
    if userType != "admin" and userType != "merchant":
        return JSONResponse(status_code=404, content={"detail": "you lack privilages"})
    try:
        banner= db.query(Banner).filter(Banner.bannerid == bannerId, Banner.status == 0)
        if userType == "merchant":
            getMerchant = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
            if getMerchant is None:
                return JSONResponse(status_code=404, content={"detail": "unable to retrieve merchant"})
            banner = banner.filter(Banner.merchantId == getMerchant)
        banner = banner.first()
        if banner is None:
            return JSONResponse(status_code=404, content={"detail": "data not found"})
        banner.status = 1
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "data successfully deleted"})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"detail": "Failed to delete banner"})
    