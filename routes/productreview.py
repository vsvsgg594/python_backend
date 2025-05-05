from typing import Optional
from fastapi import APIRouter,Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models import productReviewTable
from base_model import ProductReviewCreate  # Pydantic models
from database import db_dependency
from routes.token import decode_token,bearer_scheme

router = APIRouter()

@router.post("/add-product-review", tags=["Review"],)
async def add_product_review(
    review_data: ProductReviewCreate,  # Use Pydantic model for request data
    db: db_dependency,token:Optional[str] = Depends(bearer_scheme) # Dependency to get the DB session
):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "customer":
        return JSONResponse(status_code=403, content={"detail": "you lack login privilages"})
    try:
        # Create a new product review instance using the SQLAlchemy model
        review = productReviewTable(
            productId=review_data.productId,
            rating=review_data.rating,
            comment=review_data.comment,
            reviewedByUser=userId 
            
        )
        
        # Add the review to the session and commit to the database
        db.add(review)
        db.commit()
       
        
        # Return the created review
        return JSONResponse(status_code=200, content={"detail": " productreview added successfully"})
    
    except Exception as e:
        # Log the error (for debugging purposes)
        print(f"Error occurred: {e}")
        
        # Return an error response
        return JSONResponse(status_code=500, detail="Unable to add product review")
       

@router.delete("/delete-product-review/{productReviewId}", tags=["Review"])
async def deletebanner(productReviewId:int, db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    product = db.query(productReviewTable).filter(productReviewTable.productReviewId ==productReviewId, productReviewTable.status == 0).first()
    if product is None:
        return JSONResponse(status_code=404,content={"detail": "product not found"})
    product.status = 1
    db.commit()
    return JSONResponse(status_code=200, content={"detail": "productreview succefully"})