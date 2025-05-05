from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from base_model import CouponCreate,CouponDetail
from fastapi import APIRouter, Depends, HTTPException
from database import db_dependency
from models import couponsTable
from routes.token import bearer_scheme,decode_token
from typing import Optional
import uuid
router=APIRouter()
@router.post("/create-coupon", tags=["Coupons"])
async def create_coupon(coupon: CouponCreate, db:db_dependency, token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token

        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"message": "You lack admin privileges"})
        
        code = str(uuid.uuid4()).replace("-", "")[:10].upper()
        # Check if a coupon with the same code already exists
        existing_coupon = db.query(couponsTable).filter(couponsTable.code == code).first()
        if existing_coupon:
            return JSONResponse(status_code=400, content={"message": "A coupon with this code already exists"})

        # Generate a unique coupon code if not provided
        

        # Create the new coupon entry
        db_coupon = couponsTable(
            couponname=coupon.couponname,
            typeOfCoupon=coupon.typeOfCoupon,
            price=coupon.price,
            description=coupon.description,
            startingdate=coupon.startingdate,
            endingdate=coupon.endingdate,
            maxValue=coupon.maxValue,
            maxAllowedUsers=coupon.maxUsers,
            minOrderAmount=coupon.minOrder,
            UsersCount=coupon.UsersCount,
            allowToUseMultipleTimes=coupon.allowToUseMultipleTimes,
            allowLoyalityPointsRedeem=coupon.allowLoyalityPointsRedeem,
            allowLoyalityPointsEarned=coupon.allowLoyalityPointsEarned,
            code=code  # Assign the generated or provided code
        )
        
        db.add(db_coupon)
        db.commit()
        db.refresh(db_coupon)

        return JSONResponse(status_code=201, content={"message": "Coupon created successfully"})
    
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"message": "An error occurred", "details": str(e)})


# Read all Coupons
@router.post("/viewall-coupons",tags=["Coupons"])
def read_coupons(cd:CouponDetail, db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        # userType = decoded_token.get('userType')
        # if userType != "admin":
        #     return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"}) 
        limit = int(cd.limit) if cd.limit else 10
        page = int(cd.page) if cd.page else 1
        offset = limit * (page - 1)
        data= db.query(couponsTable).limit(limit).offset(offset).all()
        if data is None:
            return JSONResponse(status_code=200, content={"detail": []})
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(data)})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400,content={"detail":[]})



@router.put("/edit-coupon/{coupon_id}", tags=["Coupons"])
async def edit_coupon(coupon_id: int, coupon: CouponCreate, db:db_dependency, token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token

        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"message": "You lack admin privileges"})

        # Fetch the existing coupon from the database
        db_coupon = db.query(couponsTable).filter(couponsTable.couponId == coupon_id).first()
        if db_coupon is None:
            return JSONResponse(status_code=404, content={"message": "Coupon not found"})

        # Update fields only if they are not empty or None
        if coupon.couponname !="":
            db_coupon.couponname = coupon.couponname
        if coupon.typeOfCoupon :  # Assuming this can be an int
            db_coupon.typeOfCoupon = coupon.typeOfCoupon
        if coupon.price !="":
            db_coupon.price = coupon.price
        if coupon.description !="":
            db_coupon.description = coupon.description
        if coupon.startingdate !="":
            db_coupon.startingdate = coupon.startingdate
        if coupon.endingdate !="":
            db_coupon.endingdate = coupon.endingdate
        if coupon.maxValue !="":
            db_coupon.maxValue = coupon.maxValue
        if coupon.maxUsers !="":
            db_coupon.maxAllowedUsers = coupon.maxUsers
        if coupon.minOrder !="":
            db_coupon.minOrderAmount = coupon.minOrder
        if coupon.UsersCount !="":
            db_coupon.UsersCount = coupon.UsersCount
        if coupon.allowToUseMultipleTimes !="":
            db_coupon.allowToUseMultipleTimes = coupon.allowToUseMultipleTimes
        if coupon.allowLoyalityPointsRedeem !="":
            db_coupon.allowLoyalityPointsRedeem = coupon.allowLoyalityPointsRedeem
        if coupon.allowLoyalityPointsEarned !="":
            db_coupon.allowLoyalityPointsEarned = coupon.allowLoyalityPointsEarned
            

        # Commit the changes
        db.commit()
        db.refresh(db_coupon)

        return JSONResponse(status_code=200, content={"message": "Coupon updated successfully"})
    
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"message": "An error occurred", "details": str(e)})

# Delete Coupon
@router.delete("/delete-coupon/{coupon_id}",tags=["Coupons"])
def delete_coupon(coupon_id: int, db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    try:
        db_coupon = db.query(couponsTable).filter(couponsTable.couponId == coupon_id).first()
        if db_coupon is None:
            return JSONResponse(status_code=404,content={"detail":"Coupon not found"})
        
        db.delete(db_coupon)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "Coupon deleted"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to  delete coupon"})
        