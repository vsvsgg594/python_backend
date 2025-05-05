
from routes.helpers import haversine
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from database import db_dependency
from base_model import addressModel,userProfileModel, userDetailsModel, userLoc, merchantReviewCreate,deleteproductmodel
import models
from fastapi.encoders import jsonable_encoder
from routes.token import decode_token, bearer_scheme
from sqlalchemy.orm import joinedload
from datetime import datetime
from sqlalchemy import func


router = APIRouter()
# Set up logging

@router.post("/add-address", tags=['Address'])
async def add_address(ad: addressModel, db: db_dependency, token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        user_type = decoded_token.get('userType')
        if user_type != "customer":
            raise HTTPException(status_code=403, detail="You lack admin privileges")

        # Check if the new address is set to be the default
        if ad.isDefault == 1:
            # Find the existing default address
            db.query(models.addressTable).filter(models.addressTable.isDefault == 1).update({models.addressTable.isDefault: 0})
            db.commit()
        # Add the new address
        db_address = models.addressTable(**ad.model_dump())
        db.add(db_address)
        db.commit()

        return JSONResponse(status_code=201, content={"detail": "Address added successfully"})
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":"Failed to add address"})


@router.post("/edit-address/{address_id}", tags=['Address'])
async def edit_address(address_id: int, ad: addressModel, db: db_dependency, token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        user_type = decoded_token.get('userType')
        if user_type != "customer":
            raise HTTPException(status_code=403, detail="You lack admin privileges")
        userId = decoded_token.get('userId')
        # Find the address to be updated
        db_address = db.query(models.addressTable).filter(models.addressTable.addressId == address_id).first()
        if db_address is None:
            raise HTTPException(status_code=404, detail="Address not found")

        # Check if the update is trying to set this address as default
        if ad.isDefault == 1:
            # If the address being updated is already default, no need to update others
            if db_address.isDefault != 1:
                # Set all other addresses to not default
                db.query(models.addressTable).filter(models.addressTable.addressId != address_id,models.addressTable.userId == userId).update({models.addressTable.isDefault: 0})
                db.commit()

        # Prevent changing an existing default address to not default
        if db_address.isDefault == 1 and ad.isDefault == 0:
            raise HTTPException(status_code=400, detail="Cannot change the current default address to not default")

        # Update the record with new data
        for key, value in ad.model_dump().items():
            setattr(db_address, key, value)

        db.commit()

        return JSONResponse(status_code=200, content={"detail": "Address updated successfully"})
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        print(f"Error updating address: {e}")
        raise HTTPException(status_code=500, detail="Failed to update address")

 

@router.post("/delete-address/{address_id}", tags=['Address'])
async def delete_address(address_id: int, db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    userType = decoded_token.get('userType')
    if userType != "customer":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    try:
        db_address = db.query(models.addressTable).filter(models.addressTable.addressId == address_id).first()
        if db_address is None:
            return JSONResponse(status_code=404, detail="Address not found")

        db.delete(db_address)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "Address deleted successfully"})
    except Exception as e:
        db.rollback()
        print(e)  # Consider using a logging framework instead of print
        raise JSONResponse(status_code=500,content={"detail":"Failed to delete address"})


@router.get("/view-address", tags=['Address'])
async def view_addresses(db: db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "customer":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    try:
        # Retrieve and sort addresses from the database
        addresses = db.query(models.addressTable).filter(models.addressTable.userId == userId).order_by(models.addressTable.isDefault.desc()).all()  # Default address first

        return JSONResponse(status_code=200, content={"detail":jsonable_encoder(addresses)})

    except Exception as e:
        db.rollback()
        # Log the exception with a logging framework for better traceability
        print(str(e))
        # Raise HTTPException with a 500 status code
        raise JSONResponse(status_code=500,content={"detail":"Failed to retrieve addresses"} )
    

@router.post("/view-userprofile",summary="admin can view data of all users a user can view his own data", tags=["All Users"])
async def viewUserProfile(up:userProfileModel,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "customer" and userType != "admin" and userType != "merchant" and userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    try:
        if userType != "admin":
            userId = decoded_token.get('userId')
        else:
            userId = int(up.userId)

        fetch = db.query(models.users).options(joinedload(models.users.userrelation2),joinedload(models.users.userrelation1),joinedload(models.users.userrelation10),joinedload(models.users.userrelation9)).filter(models.users.userId == userId).first()

        return JSONResponse(status_code=200, content={"detail":jsonable_encoder(fetch)})
    
    except Exception as e:
        db.rollback()
        # Log the exception with a logging framework for better traceability
        print(str(e))
        # Raise HTTPException with a 500 status code
        return JSONResponse(status_code=500, content={"detail":[]})


@router.post("/add-userprofile", tags=["Users"])
async def addUserProfile(up:userDetailsModel,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "customer" and userType != "merchant" and userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    try:
        fetch = db.query(models.userDetailsTable).filter(models.userDetailsTable.userId == userId).first()
        if fetch is not None:
            return JSONResponse(status_code=200, content={"detail":"user details already present"})
        addDetails = models.userDetailsTable(userId= userId,**up.model_dump())
        db.add(addDetails)
        db.commit()
        return JSONResponse(status_code=200, content={"detail":"user details added successfully"})
    except Exception as e:
        db.rollback()
        # Log the exception with a logging framework for better traceability
        print(str(e))
        # Raise HTTPException with a 500 status code
        return JSONResponse(status_code=500, content={"detail":"unable to add user details"})

@router.post("/edit-userprofile", tags=["Users"])
async def editUserProfile(up:userDetailsModel,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "customer" and userType != "merchant" and userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"}) 
    try:
        fetch = db.query(models.userDetailsTable).filter(models.userDetailsTable.userId == userId).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail": "user details not found"})
        if up.username !="":
            fetch.userName = up.username
        if up.userdob !="":
            fetch.userDOB = up.userdob 
        if up.bankAccountHolder != "":
            fetch.bankAccountHolder = up.bankAccountHolder
        if up.bankAccountNumber != "":
            fetch.bankAccountNumber = up.bankAccountNumber
        if up.upiId != "":
            fetch.upiId = up.upiId
        if up.bankBranch != "":
            fetch.bankBranch = up.bankBranch
        if up.bankIfscCode != "":
            fetch.bankIfscCode = up.bankIfscCode

        db.commit ()
        return JSONResponse(status_code=200, content={"detail":"user details updated successfully"})
    except Exception as e:
       
        print(str(e))
        return JSONResponse(status_code=500, content={"detail":"unable to update user details"})
    

@router.post("/user-home", tags=["Users"])
async def userHome(ul:userLoc,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "customer":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"}) 
    
    try:
        currentTime = datetime.now()

        home = {}
        
        category = db.query(models.categoryTable).options(joinedload(models.categoryTable.categoryimagerelation),joinedload(models.categoryTable.categoryrelation1).joinedload(models.subCategoryTable.subcategoryImagerelation)).filter(models.categoryTable.status == 0).all()
        # for cat in category:
        #     cat.categoryrelation1 = [sub for sub in category.categoryrelation1 if sub.status == 0]
        banner = db.query(models.Banner).options(joinedload(models.Banner.bannergallery)).filter(models.Banner.status == 0, models.Banner.addToHome == 1, models.Banner.bannervalidity > currentTime).all()
        
            
        viewMerchants = db.query(models.merchantTable).options(joinedload(models.merchantTable.merchantImage)).limit(10).all()

        nearest_restaurants = []

        for merchant in viewMerchants:
            
            distance = haversine(float(ul.latitude), float(ul.longitude), float(merchant.latitude), float(merchant.longitude))
            nearest_restaurants.append({
                "merchantId":merchant.merchantId,
                "shopName": merchant.shopName,
                "Distance": distance,
                "image": merchant.merchantImage
            })

            # Sort by distance
            nearest_restaurants.sort(key=lambda x: x["Distance"])

            # Get top N nearest
            top_n = nearest_restaurants[:5]  # For example, top 5

        home = {
            "category": category,
            "banner": banner,
            "topRestaurants": top_n
        }
        return JSONResponse(status_code=200, content={"detail":jsonable_encoder(home)})
    except Exception as e:
       
        print(str(e))
        return JSONResponse(status_code=500, content={"detail":{}})

# @app.get("/recommendations/", response_model=List[Recommendation])
# def get_recommendations(token: str, db: Session = Depends(get_db)):
#     user_id = decode_token(token)
    
#     if user_id is None:
#         raise HTTPException(status_code=403, detail="Could not validate credentials")

#     # Fetch all keywords searched by this user
#     searched_keywords = db.query(UserSearch.keyword).filter(UserSearch.userId == user_id).all()
    
#     if not searched_keywords:
#         return []

#     # Assuming simple recommendations based on the searched keywords
#     # You might implement a more complex logic based on your needs
#     recommendations = db.query(UserSearch.keyword).filter(
#         UserSearch.keyword.in_([kw[0] for kw in searched_keywords])
#     ).distinct().all()

#     return [{"keyword": rec[0]} for rec in recommendations]


@router.post("/add-merchantreview", tags=["Users"])
async def addmerchantReview(mr:merchantReviewCreate,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "customer":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"}) 
    
    try:
        checkIfMerchantAlreadyRated = db.query(models.merchantReviewTable).filter(models.merchantReviewTable.merchantId == mr.merchantId, models.merchantReviewTable.reviewedByUser == userId).first()
        if checkIfMerchantAlreadyRated is not None:
            return JSONResponse(status_code=200, content={"detail":"you already added merchant review"})
       
        addReview = models.merchantReviewTable(merchantId=mr.merchantId,rating=mr.rating,comment=mr.comment,reviewedByUser= userId)
        db.add(addReview)
        db.flush()
        average_rating = db.query(func.avg(models.merchantReviewTable.rating)).filter(models.merchantReviewTable.merchantId == mr.merchantId).scalar()
        getMerchant = db.query(models.merchantTable).filter(models.merchantTable.merchantId == mr.merchantId).first()
        getMerchant.rating = average_rating
        db.commit()
        return JSONResponse(status_code=200, content={"detail":"merchant review added"})
    except Exception as e:
        db.rollback()
        print(str(e))
        return JSONResponse(status_code=500, content={"detail":"unable to add merchant review"})
    
@router.get("/view-merchantreview/{merchantId}", tags=["Users"])
async def addmerchantReview(merchantId:int,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    
    
    try:
        fetch = db.query(models.merchantTable).options(joinedload(models.merchantTable.merchantreview)).filter(models.merchantTable.merchantId == merchantId).first()
        if fetch is None:
            return JSONResponse(status_code=200, content={"detail":[]})
        return JSONResponse(status_code=200, content={"detail":jsonable_encoder(fetch)})
    except Exception as e:
        db.rollback()
        print(str(e))
        return JSONResponse(status_code=500, content={"detail":"unable to add merchant review"})