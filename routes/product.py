from fastapi import APIRouter, Depends
from database import db_dependency
from typing import Optional
from routes.token import decode_token, bearer_scheme
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload
from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_, func
from base_model import *
from models import *
from routes.helpers import haversine

router = APIRouter()

@router.post("/add-product", tags=["Product"])
async def addProduct(pm:productModel,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin" and userType != "merchant":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    userId = decoded_token.get('userId')

    try:
        #merchantId = ""
        if pm.merchantId != "":
            merchantId = int(pm.merchantId)
            #fetch = db.query(productsTable).filter(productsTable.productName == pm.productName, productsTable.merchantId == merchantId).first()
        # if userType == "merchant":
        #     getmerchant = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
        #     merchantId = getmerchant
        fetch = db.query(productsTable).filter(productsTable.productName == pm.productName, productsTable.merchantId == merchantId).first()
        if fetch is not None:
            return JSONResponse(status_code=403, content={"detail": " a product is already present with this name for the merchant"})

        getsubcategory = db.query(subCategoryTable.subcategoryName).filter(subCategoryTable.subCategoryId == pm.subCategoryId).scalar()
        if getsubcategory is None:
            return JSONResponse(status_code=404, content={"detail": "subcategory not found"})

        sku = pm.productName + "-" + getsubcategory + "-" + str(pm.merchantId)

        productadd = productsTable(sku=sku, productName= pm.productName, description= pm.description, costPrice=pm.costPrice,price= pm.price, preparationTime= pm.preparationTime, longDescription= pm.longDescription, minimumQuantity= pm.minimumQuantity, maximumQuantity = pm.maximumQuantity,isVeg = pm.isVeg,categoryId= pm.categoryId, subCategoryId= pm.subCategoryId, merchantId= merchantId, priorityOrder = pm.priorityOrder)
        db.add(productadd)
        db.flush()
       
        if len(pm.tax) > 0:
            for tax in pm.tax:
                getTaxAmount = db.query(taxTable).filter(taxTable.taxId == tax, taxTable.status == 0, taxTable.deleteStatus == 0).first()
                if getTaxAmount is None:
                    return JSONResponse(status_code=404, content={"detail": "tax not found"})
                taxType = getTaxAmount.taxType
                taxPrice = getTaxAmount.tax
                if taxType == 1:
                    taxtotal = taxPrice
                elif taxType == 2:
                    taxtotal = pm.price * (taxPrice / 100)
                else:
                    return JSONResponse(status_code=404, content={"detail": "invalid tax type"})
                    
                #taxAmount = pm.price * (tax / 100)
                addTax = productTaxTable(productId = productadd.productId, taxId = tax, taxAmount = taxtotal)
                db.add(addTax)
        if len(pm.images) > 0:
            for image in pm.images:
                addImage = productImages(productId = productadd.productId,imageId= image)
                db.add(addImage)
        if len(pm.tags) > 0:
            #db.query(searchTable).filter(searchTable.productId == productadd.productId).delete()
            for tag in pm.tags:
                addTag = searchTable(productId=productadd.productId,searchTag=tag)
                db.add(addTag)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "product added successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to add product"})

    
    


@router.put("/edit-product/{productId}", tags=["Product"])
async def editProduct(productId:int,pm:productEditModel,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin" and userType != "merchant":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    userId = decoded_token.get('userId')

    
    try:
        fetch = db.query(productsTable).filter(productsTable.productId == productId).first()
        if userType == "merchant":
            # getmerchant = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
            fetch =db.query(productsTable).filter(productsTable.productId == productId, productsTable.merchantId == int(pm.merchantId)).first()  
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail": "item not found"})
        price = fetch.price
        isAvailable = fetch.isAvailable

        getsubcategory = db.query(subCategoryTable.subcategoryName).filter(subCategoryTable.subCategoryId == fetch.subCategoryId).scalar()

        if pm.subCategoryId != "":
            getsubcategory = db.query(subCategoryTable.subcategoryName).filter(subCategoryTable.subCategoryId == pm.subCategoryId).scalar()
            if getsubcategory is None:
                return JSONResponse(status_code=404, content={"detail": "subcategory not found"})
        
        checkProductName = db.query(productsTable).filter(productsTable.productName == pm.productName, productsTable.productId != productId, productsTable.merchantId == fetch.merchantId,productsTable.status == 0).first()
        if checkProductName is not None:
            return JSONResponse(status_code=406 , content={"detail": "a product already has this name"})
        if pm.productName != "":
            fetch.sku = pm.productName + "-" + getsubcategory + "-" + str(fetch.merchantId)
        getproduct = db.query(productsTable).filter(productsTable.productId == productId).first()
        for attr, value in pm.model_dump().items():
            if value == "":
                    value = None 
            if value is not None:
                setattr(getproduct, attr, value)
        
        # if pm.price != "":
        #     price = int(pm.price)
        # if pm.isAvailable != "":
        #     isAvailable = int(pm.isAvailable)
        if len(pm.images) > 0:
            # getimages = db.query(productImages).filter(productImages.productId == productId).all()
            # for existImages in getimages:
            #     db.delete(existImages)
            # Delete all images associated with the specified productId
            db.query(productImages).filter(productImages.productId == productId).delete()#synchronize_session=False
            #db.commit()  # Commit the transaction

            for image in pm.images:
                addImage = productImages(productId = productId,imageId= image)
                db.add(addImage)

        if len(pm.tax) > 0:
            # Delete all images associated with the specified productId
            db.query(productTaxTable).filter(productTaxTable.productId == productId).delete()
           # db.commit()  # Commit the transaction

            for tax in pm.tax:
                getTaxAmount = db.query(taxTable).filter(taxTable.taxId == tax, taxTable.status == 0, taxTable.deleteStatus == 0).first()
                if getTaxAmount is None:
                    return JSONResponse(status_code=404, content={"detail": "tax not found"})
                taxType = getTaxAmount.taxType
                taxPrice = getTaxAmount.tax
                if taxType == 1:
                    taxtotal = taxPrice
                elif taxType == 2:
                    taxtotal = price * (taxPrice / 100)
                else:
                    return JSONResponse(status_code=404, content={"detail": "invalid tax type"})
                    
                #taxAmount = pm.price * (tax / 100)
                addTax = productTaxTable(productId =productId, taxId = tax, taxAmount = taxtotal)
                db.add(addTax)

        if len(pm.tags) > 0:
            db.query(searchTable).filter(searchTable.productId == productId).delete()
            for tag in pm.tags:
                addTag = searchTable(productId=productId,searchTag=tag)
                db.add(addTag)
        
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "product updated successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to update product"})
    


@router.get("/viewsingle-product/{productId}", tags=["Product"])
async def viewSingleProduct(productId:int,db:db_dependency):

    try:
        products = {'selectedProduct': [], 'similarProducts': [], 'productFromMerchant': []}
        
        fetch = db.query(productsTable).options(joinedload(productsTable.productstablerelation1).joinedload(merchantTable.merchantImage),joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2),joinedload(productsTable.productstablerelation5),joinedload(productsTable.productstablerelation7),joinedload(productsTable.productstablerelation6).joinedload(productReviewTable.productreviewrelation2),joinedload(productsTable.productstablerelation2),joinedload(productsTable.productstablerelation3), joinedload(productsTable.productstabletax).joinedload(productTaxTable.producttaxrelation),joinedload(productsTable.searchproduct)).filter(productsTable.productId == productId,productsTable.status == 0).first()
        if fetch is None:
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(products)})
        products["selectedProduct"].append(fetch)
        similarProducts = db.query(productsTable).distinct(productsTable.productName).options(joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2),joinedload(productsTable.productstablerelation2),joinedload(productsTable.productstablerelation3)).filter(productsTable.productId != productId,productsTable.status == 0,productsTable.subCategoryId == fetch.subCategoryId).limit(5).all()
        if similarProducts is not None:
            products["similarProducts"].append(similarProducts)
        productsFromSameMerchant = db.query(productsTable).distinct(productsTable.productName).options(joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2),joinedload(productsTable.productstablerelation2),joinedload(productsTable.productstablerelation3)).filter(productsTable.productId != productId,productsTable.status == 0,productsTable.merchantId == fetch.merchantId).limit(5).all()
        if productsFromSameMerchant is not None:
            products["productFromMerchant"].append(productsFromSameMerchant)
        
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(products)})

    except Exception as e:
        print(str(e))
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": []})
    

#customers has to give their coordinates to see the distance to the product restaurant
#admin merchant and deliveryAgent does not need to do that

@router.post("/viewall-products", tags=["Product"])
async def viewAllProducts(db:db_dependency,p:productPagination, token:Optional[str] = Depends(bearer_scheme)):

    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "admin" and userType != "merchant" and userType != "customer" and userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
   
    limit = int(p.limit) if p.limit else 10
    page = int(p.page) if p.page else 1
    offset = limit * (page - 1)

    try:
        
        if p.search != "":

            search_pattern = f"%{p.search}%"
            search_results = db.query(searchTable).filter(
                searchTable.searchTag.ilike(search_pattern)
            ).limit(limit).offset(offset).all()

            totalCount = db.query(searchTable).filter(
                searchTable.searchTag.ilike(search_pattern)
            ).count()
            
            
            product_ids = [result.productId for result in search_results]
            #merchant_ids = [result.merchantId for result in search_results]

            # merchantList = []
            # if merchant_ids:
            #     for merchantId in merchant_ids:
            #         mymerchant = db.query(merchantTable).options(joinedload(merchantTable.merchantImage)).filter(merchantTable.merchantId == merchantId).first()
            #         distance = ""
            #         if userType == "customer":
            #             distance = haversine(float(p.latitude), float(p.longitude), float(mymerchant.latitude), float(mymerchant.longitude))
            #         merchantList.append({"merchants":mymerchant,"Distance":distance})


            # Fetch products based on the collected product IDs and order by priority
            if product_ids:
                products = db.query(productsTable).options(
                    joinedload(productsTable.productstablerelation1).joinedload(merchantTable.merchantImage),
                    joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2)
                )
                
                if userType == "merchant":
                    # getmerchant = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
                    products = products.filter(productsTable.productId.in_(product_ids), productsTable.merchantId == int(p.merchantId))
                else:
                    products = products.filter(productsTable.productId.in_(product_ids))

                #products = products.filter(productsTable.isAvailable )

                # totalCount = products.count()
             
                products =products.filter(productsTable.isAvailable == 0, productsTable.status == 0).order_by(productsTable.priorityOrder.desc()).all()  # Order by priority
                #totalCount = 1
                productArray = []
                if userType == "customer":
                    
                    if products is not None:
                        for pro in products:
                            distance = haversine(float(p.latitude), float(p.longitude), float(pro.productstablerelation1.latitude), float(pro.productstablerelation1.longitude))
                            if pro.productstablerelation1.servingRadius >= distance:
                    
                                productArray.append({
                                "product": pro,
                                "Distance": distance
                            })

                    return JSONResponse(status_code=200, content={"detail": jsonable_encoder(productArray), "totalCount":totalCount})
                if products is not None:
                        for pro in products:
                            productArray.append({
                            "product": pro,
                            "Distance": "" #distance
                        })
                return JSONResponse(status_code=200, content={"detail": jsonable_encoder(productArray), "totalCount":totalCount})
            else:
                return JSONResponse(status_code=200, content={"detail": []})

          

        fetch = db.query(productsTable).options(joinedload(productsTable.productstablerelation1).joinedload(merchantTable.merchantImage),joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2)).filter(productsTable.status == 0)

        if p.category != "":
            fetch = fetch.filter(productsTable.categoryId == int(p.category))
        if p.subCategory != "":
            fetch = fetch.filter(productsTable.subCategoryId == int(p.subCategory))
        if p.isVeg != "":
            fetch = fetch.filter(productsTable.isVeg == int(p.isVeg))
        if p.merchantId != "":
            fetch = fetch.filter(productsTable.merchantId == int(p.merchantId))
        if userType == "merchant":
            # getmerchant = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
            fetch = fetch.filter(productsTable.merchantId == int(p.merchantId))
        fetch = fetch.filter(productsTable.isAvailable == 0, productsTable.status == 0)
        totalCount = fetch.count()
        fetch = fetch.group_by(productsTable.productId,productsTable.productName).order_by(func.max(productsTable.priorityOrder).desc()).limit(limit).offset(offset).all()
        result = []
        if userType == "customer":
            
            for product in fetch:
                distance = haversine(float(p.latitude), float(p.longitude), float(product.productstablerelation1.latitude), float(product.productstablerelation1.longitude))
                #product_dict = jsonable_encoder(product)  # Encode the product object
                # product_dict['max_priority'] = max_priority  # Add the max_priority to the dict
                if product.productstablerelation1.servingRadius >= distance:
                    result.append({"product":product, "Distance":distance})


            return JSONResponse(status_code=200, content={"detail":jsonable_encoder(result), "totalCount":totalCount})
        for product in fetch:
            result.append({"product":product, "Distance":""})

        return JSONResponse(status_code=200, content={"detail":jsonable_encoder(result), "totalCount":totalCount})
        

    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": []})

    


@router.delete("/delete-product/{productId}", tags=["Product"])
async def deleteProduct(productId:int,dm:deleteproductmodel,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin" and userType != "merchant":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    userId = decoded_token.get('userId')
    
    fetchproduct = db.query(productsTable).filter(productsTable.productId == productId, productsTable.status == 0).first()
    if userType == "merchant":
        # getmerchant = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
        fetchproduct = db.query(productsTable).filter(productsTable.productId == productId, productsTable.status == 0, productsTable.merchantId == int(dm.merchantId)).first()

    if fetchproduct is None:
        return JSONResponse(status_code=404, content={"detail": "product not found"})
    fetchproduct.status = 1
    db.commit()
    return JSONResponse(status_code=200, content={"detail": "product successfully deleted"})
    
    


@router.post("/add-product-schedule/{productId}", tags=["Product"])
async def addProductSchedule(productId:int,ps:productScheduleModel,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    try:
        fetch = db.query(productScheduleTable).filter(productScheduleTable.productId == productId).first()
        if fetch is not None:
            return JSONResponse(status_code=403, content={"detail": "schedule already present for this item"})
        for i in ps.times:
            addschedule = productScheduleTable(productId= productId,startTime= i.startTime, endTime= i.endTime,days=i.day)
            db.add(addschedule)
        

        productadd = productAvailabilityTable(productId=productId,isAvailable=int(ps.isAvailable),orderAcceptanceTime=ps.orderAcceptanceTime)
        db.add(productadd)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "product schedule added successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to add product schedule"})

    

    


@router.put("/edit-product-schedule/{productId}", tags=["Product"])
async def editProductSchedule(productId:int,ps:productScheduleEdit,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    try:
        if len(ps.times) > 0:
            fetch = db.query(productScheduleTable).filter(productScheduleTable.productId == productId).first()
            if fetch is None:
                return JSONResponse(status_code=403, content={"detail": "product schedule not found"})
            db.delete(fetch)
            for i in ps.times:
                addschedule = productScheduleTable(productId= productId,startTime= i['startTime'], endTime= i['endTime'],days=i['day'])
                db.add(addschedule)
        
        getAvailability = db.query(productAvailabilityTable).filter(productAvailabilityTable.productId == productId).first()
        if getAvailability is None:
            return JSONResponse(status_code=404, content={"detail":"product availability not found"})
        if ps.isAvailable != "":
            getAvailability.isAvailable = int(ps.isAvailable)
        if ps.orderAcceptanceTime != "":
            getAvailability.orderAcceptanceTime = ps.orderAcceptanceTime
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "product schedule updated successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to update product schedule"})
    


@router.post("/search-product", tags=["Product"])
async def searchProduct(db:db_dependency,s:searchModel, token:Optional[str] = Depends(bearer_scheme)):

    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "admin" and userType != "merchant" and userType != "customer" and userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
   

    try:
        
        merchants = []
        if s.isVeg != "":
            fetch = db.query(productsTable.merchantId).filter(productsTable.isVeg == int(s.isVeg)).all()
            merchants.extend([merchant_id[0] for merchant_id in fetch])
        if s.subCategory != "":
            fetch = db.query(productsTable.merchantId).filter(productsTable.subCategoryId == int(s.subCategory)).all()
            merchants.extend([merchant_id[0] for merchant_id in fetch])
        if s.category != "":
            fetch = db.query(productsTable.merchantId).filter(productsTable.categoryId == int(s.category)).all()
            merchants.extend([merchant_id[0] for merchant_id in fetch])
        if s.search != "":
            search_pattern = f"%{s.search}%"
            search_results = db.query(searchTable).filter(
                searchTable.searchTag.ilike(search_pattern)
            ).all()

            
            product_ids = [result.productId for result in search_results if result.merchantId is None]
            merchants = [result.merchantId for result in search_results if result.productId is None]

            for product in product_ids:
                
                merchantId = db.query(productsTable.merchantId).filter(productsTable.productId == product, productsTable.status == 0, productsTable.isAvailable == 0).scalar()
                merchants.append(merchantId)
        unique = list(set(merchants))
        merchantArray = []
        if userType == "customer":
            if unique:
                for m in unique:
                    mymerchant = db.query(merchantTable).options(joinedload(merchantTable.merchantImage)).filter(merchantTable.merchantId == m, merchantTable.status == 0, merchantTable.shopStatus == 0).first()
                    distance = haversine(float(s.latitude), float(s.longitude), float(mymerchant.latitude), float(mymerchant.longitude))

                    merchantArray.append({"product":mymerchant, "Distance": distance})
                return JSONResponse(status_code=200, content={"detail": jsonable_encoder(merchantArray)})
            else:
                return JSONResponse(status_code=200, content={"detail": []})

        if unique:
            for m in unique:
                mymerchant = db.query(merchantTable).options(joinedload(merchantTable.merchantImage)).filter(merchantTable.merchantId == m).first()
                # distance = haversine(float(s.latitude), float(s.longitude), float(mymerchant.latitude), float(mymerchant.longitude))

                merchantArray.append({"product":mymerchant})
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(merchantArray)})
        else:
            return JSONResponse(status_code=200, content={"detail": []})
            


    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": []})