from fastapi import APIRouter, Depends
from database import db_dependency
from routes.token import decode_token, bearer_scheme, hash_password
from typing import Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload
from sqlalchemy import update
from fastapi.encoders import jsonable_encoder
from base_model import *
from models import *
from routes.helpers import generate_random_string
from sqlalchemy import select, func
from datetime import timedelta
from sqlalchemy import and_
import uuid
from routes.emailOtp import sendEmail


router = APIRouter()


@router.post("/add-category", tags=["Admin"])
async def addCategory(db:db_dependency, cb:categoryBase, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    try:
        addcat = categoryTable(categoryName=cb.categoryName,categoryImage= int(cb.categoryImage))
        db.add(addcat)
        # db.flush()
        # for subcat in cb.subCategoryNames:
        #     addsub = subCategoryTable(subcategoryName=subcat, categoryId= addcat.categoryId)
        #     db.add(addsub)
        
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "category added successfully"})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to add category"})
    

@router.put("/edit-category/{categoryId}", tags=["Admin"])
async def editCategory(categoryId: int,db:db_dependency, cb:categoryBase, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    try:
        fetch = db.query(categoryTable).filter(categoryTable.categoryId == categoryId, categoryTable.status == 0).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail":"category not found"})
        if cb.categoryName != "":
            fetch.categoryName = cb.categoryName
        if cb.categoryImage != "":
            fetch.categoryImage = int(cb.categoryImage)
        
        # if len(cb.subCategoryNames) > 0:
        #     # stmt = update(subCategoryTable).where(subCategoryTable.categoryId == categoryId).values(status = 1) #db.query(subCategoryTable).filter(subCategoryTable.categoryId == categoryId).delete()
        #     # db.execute(stmt)

        #     new_subcategories = [subCategoryTable(subcategoryName=name, categoryId=categoryId) for name in cb.subCategoryNames]
        #     print(new_subcategories)
        #     #db.add_all(new_subcategories)

        #     # for subcat in cb.subCategoryNames:
        #     #     addsub = subCategoryTable(subcategoryName=subcat, categoryId= categoryId)
        #     #     db.add(addsub)


        db.commit()
        return JSONResponse(status_code=200, content={"detail": "successfully updated"})

    except Exception as e:
        print(str(e))
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to edit category"})
    


@router.put("/edit-subcategory/{subcategoryId}", tags=["Admin"])
async def editSubcategory(subcategoryId: int,db:db_dependency, cb:subcategoryBase, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    try:
        fetch = db.query(subCategoryTable).filter(subCategoryTable.subCategoryId == subcategoryId, subCategoryTable.status == 0).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail":"category not found"})
        if cb.subcategoryName != "":
            fetch.subcategoryName = cb.subcategoryName
        if cb.subcategoryImage != "":
            fetch.subcategoryImage = int(cb.subcategoryImage)
        
    
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "successfully updated"})

    except Exception as e:
        print(str(e))
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to edit sub category"})
    

@router.post("/add-subcategory/{categoryId}", tags=["Admin"])
async def addsubCategory(categoryId:int,db:db_dependency, cb:subcategoryBase, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    try:
        addcat = subCategoryTable(categoryId= categoryId,subcategoryName=cb.subcategoryName,subcategoryImage= int(cb.subcategoryImage))
        db.add(addcat)
       
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "sub category added successfully"})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to add sub category"})
    

@router.get("/view-category", tags=["Admin"])
async def viewCategory(db:db_dependency):
    try:
       
        fetch = db.query(categoryTable).options(joinedload(categoryTable.categoryimagerelation),joinedload(categoryTable.categoryrelation1).joinedload(subCategoryTable.subcategoryImagerelation)).filter(categoryTable.status == 0).all()
        # for category in fetch:
        #     category.categoryrelation1 = [sub for sub in category.categoryrelation1 if sub.status == 0]
        if fetch is None:
            return JSONResponse(status_code=200, content={"detail":[]})
        return JSONResponse(status_code=200, content={"detail":jsonable_encoder(fetch)})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": []})


@router.delete("/delete-category/{categoryId}", tags=["Admin"])
async def deleteCategory(categoryId:int,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    try:
       
        fetch = db.query(categoryTable).filter(categoryTable.categoryId == categoryId ,categoryTable.status == 0).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail":"not found"})
        checkProducts = db.query(productsTable).filter(productsTable.categoryId == categoryId, productsTable.status == 0).first()
        if checkProducts is not None:
            return JSONResponse(status_code=406, content={"detail":"unable to delete because products found in this subcategory"})
        fetch.status = 1
        db.commit()
        return JSONResponse(status_code=200, content={"detail":"deleted successfully"})
    except Exception as e:
        print(str(e))
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to delete"})
    
@router.delete("/delete-subcategory/{subcategoryId}", tags=["Admin"])
async def deletesubCategory(subcategoryId:int,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    try:
       
        fetch = db.query(subCategoryTable).filter(subCategoryTable.subCategoryId == subcategoryId ,subCategoryTable.status == 0).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail":"not found"})
        checkProducts = db.query(productsTable).filter(productsTable.subCategoryId == subcategoryId, productsTable.status == 0).first()
        if checkProducts is not None:
            return JSONResponse(status_code=406, content={"detail":"unable to delete because products found in this subcategory"})
        # fetch.status = 1
        db.delete(fetch)
        db.commit()
        return JSONResponse(status_code=200, content={"detail":"deleted successfully"})
    except Exception as e:
        print(str(e))
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to delete"})

@router.post("/add-merchant", tags=["Admin"])
async def addMerchant(mm:merchantModel,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    try:
        if mm.handledByUser == "":
            mypass = "1234"
            password = hash_password(mypass)
            getuserName = db.query(users.userName).filter(users.userName == mm.userName).scalar()
            if getuserName is not None:
                return JSONResponse(status_code=406, content={"detail":"user exists with this username"})
            getuserEmail = db.query(users.userEmail).filter(users.userEmail == mm.userEmail).scalar()
            if getuserEmail is not None:
                return JSONResponse(status_code=406, content={"detail":"user exists with this email"})

            addtoLogin = users(userType=2,userPhone=mm.userPhone,userName=mm.userName,userEmail=mm.userEmail,password=password)
            db.add(addtoLogin)
            db.flush()

            db_subext = merchantTable(address=mm.address,displayAddress=mm.displayAddress,phoneNumber=mm.phoneNumber,shopName=mm.shopName,shopEmail=mm.shopEmail,coverImage=mm.coverImage,handledByUser=addtoLogin.userId,description=mm.description,servingRadius=mm.servingRadius,longitude=mm.longitude,latitude=mm.latitude,openingTime=mm.openingTime,closingTime=mm.closingTime)
        else:
            db_subext = merchantTable(address=mm.address,displayAddress=mm.displayAddress,phoneNumber=mm.phoneNumber,shopName=mm.shopName,shopEmail=mm.shopEmail,coverImage=mm.coverImage,handledByUser=mm.handledByUser,description=mm.description,servingRadius=mm.servingRadius,longitude=mm.longitude,latitude=mm.latitude,openingTime=mm.openingTime,closingTime=mm.closingTime)

        db.add(db_subext)
        db.flush()
        if len(mm.tags) > 0:
            for tag in mm.tags:
                addTag = searchTable(merchantId=db_subext.merchantId,searchTag=tag)
                db.add(addTag)
        db.commit()

        return JSONResponse(status_code=200 , content={"detail":"Details added successfully"})

    except Exception as e:
        db.rollback()
        db.query(merchantTable).filter(merchantTable.merchantId == db_subext.merchantId).delete()
        print(e)
        return JSONResponse(status_code=500, content={"detail":"failed to add details"})
    
@router.post("/edit-merchant", tags=["Admin"])
async def editMerchant(mm:merchantEditModel,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)): 
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "admin" and userType != "merchant":
        
        return JSONResponse(status_code=403, content={"detail": "you lack privilages"})

    merchantId = mm.merchantId
    if userType == "merchant":
        merchantId = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar() 

    try:
        
        getmerchant = db.query(merchantTable).filter(merchantTable.merchantId == merchantId).first()
        if getmerchant is None:
            return JSONResponse(status_code=404 , content={"detail":"merchant not found"})
        
        getuser = db.query(users).filter(users.userId == getmerchant.handledByUser).first()
        if getuser is None:
            return JSONResponse(status_code=404 , content={"detail":"user not found"})
        
        if mm.userName != "":
            getuserName = db.query(users.userName).filter(users.userName == mm.userName).scalar()
            if getuserName is not None:
                    return JSONResponse(status_code=406, content={"detail":"user exists with this username"})
            getuser.userName = mm.userName
        if mm.userEmail != "":
            getuserEmail = db.query(users.userEmail).filter(users.userEmail == mm.userEmail).scalar()
            if getuserEmail is not None:
                return JSONResponse(status_code=406, content={"detail":"user exists with this email"})
            getuser.userEmail = mm.userEmail
        if mm.password != "":
            password = hash_password(mm.password)
            getuser.password = password
        if mm.userPhone != "":
            getuser.userPhone = mm.userPhone


       
        if mm.address != "":
            getmerchant.address = mm.address
        if mm.shopEmail != "":
            getmerchant.shopEmail = mm.shopEmail
        if mm.shopName != "":
            getmerchant.shopName = mm.shopName
        if mm.handledByUser != "":
            getmerchant.handledByUser = mm.handledByUser
        if len(mm.tags) > 0:
            db.query(searchTable).filter(searchTable.merchantId == merchantId).delete()
            for tag in mm.tags:
                addTag = searchTable(merchantId=merchantId,searchTag=tag)
                db.add(addTag)
        if mm.openingTime != "":
            time_object = datetime.strptime(mm.openingTime, "%H:%M:%S").time()
            getmerchant.openingTime = time_object
        if mm.closingTime != "":
            times = datetime.strptime(mm.closingTime, "%H:%M:%S").time()
            getmerchant.closingTime = times
        if mm.coverImage != "":
            getmerchant.coverImage = int(mm.coverImage)
        if mm.phoneNumber != "":
            getmerchant.phoneNumber = mm.phoneNumber
        if mm.description != "":
            getmerchant.description = mm.description
        if mm.longitude != "":
            getmerchant.longitude = mm.longitude
        if mm.latitude != "":
            getmerchant.latitude = mm.latitude
        if mm.servingRadius != "":
            getmerchant.servingRadius = int(mm.servingRadius)
        if mm.displayAddress != "":
            getmerchant.displayAddress = mm.displayAddress
        if mm.status != "":
            getmerchant.status = int(mm.status)

        
        

        
        # if mm.shopStatus != "":
        #     getmerchant.shopStatus = int(mm.shopStatus)



        db.commit()

        return JSONResponse(status_code=200 , content={"detail":"Details updated successfully"})

    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":"failed to update details"})

@router.post("/admin-add-user", tags=["Admin"])
async def adminAddUser(su:adminSignupModel, db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    getuserName = db.query(users.userName).filter(users.userName == su.userName).scalar()
    if getuserName is not None:
        return JSONResponse(status_code=406, content={"detail":"user exists with this username"})
    getuserEmail = db.query(users.userEmail).filter(users.userEmail == su.userEmail).scalar()
    if getuserEmail is not None:
        return JSONResponse(status_code=406, content={"detail":"user exists with this email"})
    referralCode = uuid.uuid4().hex[:10]
    # mypass = "1234"
    mypass = uuid.uuid4().hex[:8]
    password = hash_password(mypass)
    try:
        db_user = users(userName=su.userName,userEmail=su.userEmail,userPhone=su.userPhone, password=password, referralCode=referralCode)
        db.add(db_user)
        
        db.commit()
        sendEmail(su.userEmail, mypass,"Please use the password below to sign in.","Credentials For Login to Orado")    
        return JSONResponse(status_code=200, content={"detail":"user added successfully"})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"detail":"Failed to create user"})
    

@router.post("/admin-edit-user/{userId}", tags=["Admin"])
async def adminEditUser(userId:int,su:userEditModel, db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    try:
    
        getuserdetails = db.query(users).filter(users.userId == userId).first()
        if getuserdetails is None:
            return JSONResponse(status_code=404, content={"detail":"user not found"}) 
        
        getuserName = db.query(users.userName).filter(users.userName == su.userName).scalar()
        if getuserName is not None:
            return JSONResponse(status_code=406, content={"detail":"user exists with this username"})
        getuserEmail = db.query(users.userEmail).filter(users.userEmail == su.userEmail).scalar()
        if getuserEmail is not None:
            return JSONResponse(status_code=406, content={"detail":"user exists with this email"})


        
        if su.userEmail != "":
            getuserdetails.userEmail = su.userEmail
        if su.userEmail != "":
            getuserdetails.userEmail = su.userEmail
        if su.userPhone != "":
            getuserdetails.userPhone = su.userPhone
        if su.password != "":
            getuserdetails.password = hash_password(su.password)

        db.commit()
     
        return JSONResponse(status_code=200, content={"detail":"user updated successfully"})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"detail":"Failed to updated user"})
    

@router.post("/admin-add-deliveryagent", tags=["Admin"])
async def adminAddDeliveryAgent(su:adminSignupModel, db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    getuserName = db.query(users.userName).filter(users.userName == su.userName).scalar()
    if getuserName is not None:
        return JSONResponse(status_code=406, content={"detail":"user exists with this username"})
    getuserEmail = db.query(users.userEmail).filter(users.userEmail == su.userEmail).scalar()
    if getuserEmail is not None:
        return JSONResponse(status_code=406, content={"detail":"user exists with this email"})

    referralCode = uuid.uuid4().hex[:10]
    # mypass = "1234"
    mypass = hash_password(uuid.uuid4().hex[:8])
    try:
        db_user = users(userName=su.userName,userEmail=su.userEmail,userPhone=su.userPhone, password=mypass, userType= 1,referralCode=referralCode)
        db.add(db_user)
        
        db.commit()
        sendEmail(su.userEmail, mypass,"Please use the password below to sign in.","Credentials For Login to Orado")     
        return JSONResponse(status_code=200, content={"detail":"delivery agent added successfully"})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"detail":"Failed to create delivery agent"})
    

@router.post("/admin-edit-deliveryagent/{userId}", tags=["Admin"])
async def adminEditDeliveryAgent(userId:int,su:userEditModel, db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    try:
    
        getuserdetails = db.query(users).filter(users.userId == userId).first()
        if getuserdetails is None:
            return JSONResponse(status_code=404, content={"detail":"user not found"}) 
        
        getuserName = db.query(users.userName).filter(users.userName == su.userName).scalar()
        if getuserName is not None:
            return JSONResponse(status_code=406, content={"detail":"user exists with this username"})
        getuserEmail = db.query(users.userEmail).filter(users.userEmail == su.userEmail).scalar()
        if getuserEmail is not None:
            return JSONResponse(status_code=406, content={"detail":"user exists with this email"})


        
        if su.userName != "":
            getuserdetails.userName = su.userName
        if su.userEmail != "":
            getuserdetails.userEmail = su.userEmail
        if su.userPhone != "":
            getuserdetails.userPhone = su.userPhone
        if su.password != "":
            getuserdetails.password = hash_password(su.password)

        db.commit()
     
        return JSONResponse(status_code=200, content={"detail":"delivery agent updated successfully"})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"detail":"Failed to updated delivery agent"})
  


@router.post("/view-merchants", tags=["All Users"])
async def viewMerchant(p:pagination,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    # if userType != "admin":
    #     return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    limit = int(p.limit) if p.limit else 10
    page = int(p.page) if p.page else 1
    offset = limit * (page - 1)
    try:
        fetch = db.query(merchantTable).options(joinedload(merchantTable.merchantImage))
        if p.search != "":
            search_pattern = f"%{p.search}%"
            fetch = fetch.filter(merchantTable.shopName.like(search_pattern))
        if userType != "admin":
            fetch = fetch.filter(merchantTable.status == 0, merchantTable.shopStatus == 0)
        fetch = fetch.order_by(merchantTable.merchantId.asc())
        totalCount = fetch.count()
        fetch = fetch.limit(limit).offset(offset).all()
        if fetch is None:
            return JSONResponse(status_code=200, content={"detail":[]})
        return JSONResponse(status_code=200 , content={"detail":jsonable_encoder(fetch),"totalCount":totalCount})

    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":[]})
    
@router.post("/view-merchantsingle/{merchantId}", tags=["All Users"])
async def viewMerchantSingle(merchantId:int,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    #userType = decoded_token.get('userType')
    # if userType != "admin":
    #     return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    current_time = datetime.now()
    try:
        checkbanner = db.query(Banner).filter(Banner.merchantId == merchantId,merchantTable.merchantbanner.any(Banner.status == 0), Banner.bannervalidity > current_time).first()
        if checkbanner is not None:
            fetch = db.query(merchantTable).options(joinedload(merchantTable.merchantImage), joinedload(merchantTable.merchantTableRelation1).joinedload(users.userrelation3), joinedload(merchantTable.merchanttablerelation4).joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2),joinedload(merchantTable.merchantbanner).joinedload(Banner.bannergallery)).filter(merchantTable.merchantId == merchantId, merchantTable.status == 0, merchantTable.merchantbanner.any(Banner.status == 0), merchantTable.merchantbanner.any(Banner.bannervalidity > current_time)).first() #, merchantTable.merchantbanner.any(and_(Banner.status == 0,Banner.bannervalidity > current_time))
            
        else:
            fetch = db.query(merchantTable).options(joinedload(merchantTable.merchantImage), joinedload(merchantTable.merchantTableRelation1).joinedload(users.userrelation3), joinedload(merchantTable.merchanttablerelation4).joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2)).filter(merchantTable.merchantId == merchantId, merchantTable.status == 0).first() #, merchantTable.merchantbanner.any(and_(Banner.status == 0,Banner.bannervalidity > current_time))
            
        
        if fetch is None:
            return JSONResponse(status_code=200, content={"detail":[]})
        return JSONResponse(status_code=200 , content={"detail":jsonable_encoder(fetch)})

    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":[]})
    
    

@router.post("/view-allcustomers", tags=["Admin"])
async def viewAllCustomers(p:pagination,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    limit = int(p.limit) if p.limit else 10
    page = int(p.page) if p.page else 1
    offset = limit * (page - 1)
    try:
        fetch = db.query(users).options(joinedload(users.userrelation1), joinedload(users.userrelation2), joinedload(users.userrelation3))
        if p.search != "":
            search_pattern = f"%{p.search}%"
            fetch = fetch.filter(users.userName.like(search_pattern))

        fetch = fetch.filter(users.userType == 0)
        totalCount = fetch.count()
        fetch = fetch.limit(limit).offset(offset).all()
        if fetch is None:
            return JSONResponse(status_code=200, content={"detail":[]})
        return JSONResponse(status_code=200 , content={"detail":jsonable_encoder(fetch), "totalCount":totalCount})

    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":[]})
    
@router.get("/block-unblock-merchant/{merchantId}", tags=["Admin"])
async def blockUnblockMerchant(merchantId:int,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    try:
        fetch = db.query(merchantTable).filter(merchantTable.merchantId == merchantId).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail":"merchant not found"})
        
        getstatus = fetch.shopStatus
        if getstatus == 1:
            fetch.shopStatus = 0
            message = "merchant unblocked"
        if getstatus == 0:
            fetch.shopStatus = 1
            message = "merchant blocked"
        db.commit()
        return JSONResponse(status_code=200 , content={"detail":message})

    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":"failed"})


@router.post("/admin-home", tags=["Admin"])
async def adminHome(ab:adminBase,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    try:
        currentTime = datetime.now().time()
        formatted_time = currentTime.strftime("%H:%M:%S")

        current_year = datetime.now().year
        current_month = datetime.now().month
        
        stmt = (
        select(
            func.count(merchantTable.merchantId).filter(merchantTable.status == 0, merchantTable.shopStatus == 0).label("active_merchants"),
            func.count(merchantTable.merchantId).filter(merchantTable.status == 1, merchantTable.shopStatus == 0).label("inactive_merchants"),
            func.count(merchantTable.merchantId).filter(merchantTable.openingTime < formatted_time, merchantTable.closingTime > formatted_time, merchantTable.status == 0, merchantTable.shopStatus == 0).label("openMerchants"),
            func.count(merchantTable.merchantId).filter(func.extract('year', merchantTable.addedAt) == current_year, func.extract('month', merchantTable.addedAt) == current_month, merchantTable.shopStatus == 0).label("merchantThisMonth")
        )
        )
        stmt2 =(
            select(
            func.sum(ordersTable.totalAmount).filter(ordersTable.orderStatus == 2, ordersTable.status == 0).label("sales"),
            func.count(ordersTable.orderId).filter(ordersTable.status == 1).label("cancelled"),
            func.count(ordersTable.orderId).filter(ordersTable.orderStatus == 0, ordersTable.status == 0).label("pending"),
            func.count(ordersTable.orderId).filter(ordersTable.orderStatus == 1, ordersTable.status == 0).label("dispatched"),
            func.count(ordersTable.orderId).filter(ordersTable.orderStatus == 2, ordersTable.status == 0).label("completed"),
            )
        )

        getcustomer = select(func.count(users.userId).filter(func.extract('year', users.addedAt) == current_year, func.extract('month', users.addedAt) == current_month, users.userType == 0).label("customerThisMonth"))

        result2 = db.execute(stmt2).one()
        result = db.execute(stmt).one()
        result3 = db.execute(getcustomer).one()

        merchantlist = []

        fetch = db.query(merchantTable).options(joinedload(merchantTable.merchantImage)).filter(merchantTable.shopStatus == 0).order_by(merchantTable.merchantId.asc()).limit(10).all()
        # if ab.merchantSearch != "":
        #     search_pattern = f"%{ab.merchantSearch}%"
        #     fetch = fetch.filter(merchantTable.shopName.like(search_pattern))
        
        #fetch = fetch.filter(merchantTable.shopStatus == 0).order_by(merchantTable.merchantId.asc()).limit(10).all()

        current_day = datetime.now().date()
        sixDayBefore = current_day - timedelta(days=6)

        if fetch is not None:
            merchantlist = jsonable_encoder(fetch)
        if ab.startDate != "":
            current_day = datetime.strptime(ab.startDate, "%Y-%m-%d").date()
        if ab.endDate != "":
            sixDayBefore = datetime.strptime(ab.endDate, "%Y-%m-%d").date()

        if current_day < sixDayBefore:
            return JSONResponse(status_code=406,content={"detail":"End date cannot be before start date."})

        orderData = db.query(ordersTable).options(joinedload(ordersTable.ordereduser)).order_by(ordersTable.addedAt.desc()).limit(6).all()

        date_range = [sixDayBefore + timedelta(days=i) for i in range((current_day - sixDayBefore).days + 1)]

        sales_data = db.query(func.date(ordersTable.addedAt).label("date"), func.sum(ordersTable.totalAmount).label("total_sales")).filter(ordersTable.addedAt >= sixDayBefore, ordersTable.addedAt <= current_day, ordersTable.status == 0, ordersTable.orderStatus == 2).group_by(func.date(ordersTable.addedAt)).order_by(func.date(ordersTable.addedAt)).all()
        #sale = [SalesData(date=date, total_sales=total_sales) for date, total_sales in sales_data]

        order_graph = db.query(func.date(ordersTable.addedAt).label("date"), func.count(ordersTable.orderId).label("total_orders")).filter(ordersTable.addedAt >= sixDayBefore, ordersTable.addedAt <= current_day, ordersTable.status == 0, ordersTable.orderStatus == 2).group_by(func.date(ordersTable.addedAt)).order_by(func.date(ordersTable.addedAt)).all()
        #orders = [orderGraph(date=date, total_orders=total_orders) for date, total_orders in order_graph]

        sales_dict = {date: total_sales for date, total_sales in sales_data}
        orders_dict = {date: total_orders for date, total_orders in order_graph}

        sale = [SalesData(date=date, total_sales=sales_dict.get(date, 0)) for date in date_range]
        orders = [orderGraph(date=date, total_orders=orders_dict.get(date, 0)) for date in date_range]

        getall = {
            "activeMerchants":result.active_merchants if result.active_merchants else 0,
            "inactiveMerchants": result.inactive_merchants if result.inactive_merchants else 0,
            "openMerchants": result.openMerchants if result.openMerchants else 0,
            "closedMerchants": result.active_merchants - result.openMerchants if result.active_merchants and result.openMerchants else 0,
            "orderTotalSales": result2.sales if result2.sales else 0,
            "orderPending": result2.pending if result2.pending else 0,
            "orderDispatched": result2.dispatched if result2.dispatched else 0,
            "orderCompleted": result2.completed if result2.completed else 0,
            "orderCancelled": result2.cancelled if result2.cancelled else 0,
            "merchantsThisMonth": result.merchantThisMonth if result.merchantThisMonth else 0,
            "customersThisMonth": result3.customerThisMonth if result3.customerThisMonth else 0,
            "merchantlist": merchantlist,
            "salesGraph": jsonable_encoder(sale),
            "orderGraph": jsonable_encoder(orders),
            "orderData": jsonable_encoder(orderData)
        }
       

        return JSONResponse(status_code=200, content={"detail": getall})
    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":{}})
    

@router.post("/admin-view-notifications", tags=["Admin"])
async def adminViewNotifications(p:CouponDetail,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    try:
        limit = int(p.limit) if p.limit else 10
        page = int(p.page) if p.page else 1
        offset = limit * (page - 1)
        fetch = db.query(Notification).order_by(Notification.notificationid.desc()).limit(limit).offset(offset).all()
        if fetch is None:
            return JSONResponse(status_code=200, content={"detail": []})    
        return JSONResponse(status_code=200, content={"detail": fetch})
    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":[]})