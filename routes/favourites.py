from fastapi import APIRouter, Depends
from database import db_dependency
from routes.token import decode_token, bearer_scheme
from typing import Optional
from fastapi.responses import JSONResponse
from models import wishlistTable,productsTable,productImages
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import joinedload


router = APIRouter()

@router.get("/add-to-wishlist/{productId}", tags=['Favourites'])
async def addToWishlist(productId:int,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "customer":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    
    try:
        addwish = wishlistTable(productId = productId, userId = userId)
        db.add(addwish)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "successfully added to wishlist"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to add to wishlist"})



@router.get("/view-wishlist", tags=['Favourites'])
async def viewWishlist(db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "customer":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    
    try:
        fetch = db.query(wishlistTable).options(joinedload(wishlistTable.wishlistproduct).joinedload(productsTable.productstablerelation1)).options(joinedload(wishlistTable.wishlistproduct).joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2)).filter(wishlistTable.userId == userId).all()
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(fetch)})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": []})


@router.delete("/remove-wishlist/{wishlistId}", tags=['Favourites'])
async def deleteWishlist(wishlistId:int,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "customer":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    
    try:
        fetch = db.query(wishlistTable).filter(wishlistTable.wishlistId == wishlistId, wishlistTable.userId == userId).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail": "item not found"}) 
        fetch.status = 1 
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "successfully added to wishlist"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to add to wishlist"})