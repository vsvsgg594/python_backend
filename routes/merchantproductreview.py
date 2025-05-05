from typing import Optional
from fastapi import APIRouter,Depends
from fastapi.responses import JSONResponse
from models import merchantTable, productImages, productsTable, searchTable
from base_model import merchantproductPagination  # Pydantic models
from database import db_dependency
from sqlalchemy import func
from routes.token import decode_token,bearer_scheme
from sqlalchemy.orm import joinedload
from fastapi.encoders import jsonable_encoder
router = APIRouter()
@router.post("/viewall-merchant-products",tags=["MechantProduct"])
async def viewAllProducts(db:db_dependency,p:merchantproductPagination,token:Optional[str] = Depends(bearer_scheme)):
   
    limit = int(p.limit) if p.limit else 10
    page = int(p.page) if p.page else 1
    offset = limit * (page - 1)
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "merchant":
        return JSONResponse(status_code=403, content={"detail": "you lack login privilages"})

    try:
        merchantid=db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
        if p.search != "":
            # fetch = db.query(productsTable).options(joinedload(productsTable.productstablerelation1).joinedload(merchantTable.merchantImage),joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2)).filter(productsTable.status == 0) 
            search_pattern = f"%{p.search}%"
            # # search_results = db.query(searchTable).filter(
            #     searchTable.searchTag.ilike(search_pattern)
            # ).limit(limit).all()

            # product_ids = [result.productId for result in search_results]

            # # Fetch products based on the collected product IDs and order by priority
            # if product_ids:
            products = db.query(productsTable).options(
                joinedload(productsTable.productstablerelation1).joinedload(merchantTable.merchantImage),
                joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2)
            ).filter(
                productsTable.merchantId == merchantid, 
                productsTable.status == 0,
                productsTable.productName.ilike(search_pattern) 
            ).order_by(productsTable.priorityOrder.desc()).all()  # Order by priority

            output = [jsonable_encoder(product) for product in products]

            return JSONResponse(status_code=200, content={"detail": output})
        
        products = db.query(productsTable).options(
                joinedload(productsTable.productstablerelation1).joinedload(merchantTable.merchantImage),
                joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2)
            ).filter(
                productsTable.merchantId == merchantid, 
                productsTable.status == 0
            ).order_by(productsTable.priorityOrder.desc()).all()  # Order by priority

        output = [jsonable_encoder(product) for product in products]

        return JSONResponse(status_code=200, content={"detail": output})
        
    
    #     fetch = db.query(productsTable).options(joinedload(productsTable.productstablerelation1).joinedload(merchantTable.merchantImage),joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2)).filter(productsTable.status == 0,productsTable.merchantId == int(p.merchantId))
    #     fetch = fetch.group_by(productsTable.productId,productsTable.productName).order_by(func.max(productsTable.priorityOrder).desc()).limit(limit).offset(offset).all()
    #     result = []
    #     for product in fetch:
    #         product_dict = jsonable_encoder(product)  # Encode the product object
    #         # product_dict['max_priority'] = max_priority  # Add the max_priority to the dict
    #         result.append(product_dict)


    #     return JSONResponse(status_code=200, content={"detail":result})
        

    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": []})