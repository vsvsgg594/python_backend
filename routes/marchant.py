from datetime import datetime
from fastapi import APIRouter,Depends
from fastapi.encoders import jsonable_encoder
from base_model import merchantpanel, datemo, signupModel, merchantonboarding, merchantEditMerchant
from database import db_dependency
from routes.token import decode_token, bearer_scheme
from typing import Optional
from fastapi.responses import JSONResponse
from models import ordersTable, merchantTable,users,searchTable
from sqlalchemy import select, func
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
from calendar import month_name
from routes.token import hash_password, create_access_token
import uuid


router=APIRouter()
@router.post("/merchant-home", tags=["Merchant"])
async def merchantHome(mh:merchantpanel,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    merchantIds = decoded_token.get('merchantIds')
    if userType != "merchant":
        return JSONResponse(status_code=403, content={"detail": "you lack merchant privilages"})
    if int(mh.merchantId) not in merchantIds:
        return JSONResponse(status_code=403, content={"detail": "you do not have access to this account"})
    try:

        
        stmt = (
        select(
            func.count(ordersTable.orderId).filter(ordersTable.status == 1, ordersTable.merchantId == int(mh.merchantId)).label("cancelled"),
            func.count(ordersTable.orderId).filter(ordersTable.orderStatus == 0, ordersTable.status == 0, ordersTable.merchantId == int(mh.merchantId)).label("pending"),
            func.count(ordersTable.orderId).filter(ordersTable.orderStatus == 1, ordersTable.status == 0, ordersTable.merchantId == int(mh.merchantId)).label("dispatched"),
             func.sum(ordersTable.totalAmount).filter(ordersTable.orderStatus == 2, ordersTable.status == 0, ordersTable.merchantId == int(mh.merchantId)).label("sales"),
        )
        )
        result = db.execute(stmt).one()
       
        
        start_date = datetime.strptime(mh.startdate, '%Y-%m-%d')
        end_date = datetime.strptime(mh.enddate, '%Y-%m-%d')
        if mh.startdate != "":
            start_date = datetime.strptime(mh.startdate, "%Y-%m-%d").date()
        if mh.enddate != "":
            end_date = datetime.strptime(mh.enddate, "%Y-%m-%d").date()
       

        # Query to get sales per month
        sales_data = db.query(
        func.to_char(ordersTable.addedAt, 'YYYY-MM').label("month"),
        func.sum(ordersTable.totalAmount).label("total_sales")  # Adjust this to your sales column
    ).filter(
        ordersTable.merchantId == int(mh.merchantId),
        ordersTable.addedAt >= start_date,
        ordersTable.addedAt <= end_date,
        ordersTable.status == 0,  # Assuming 0 means active or relevant status
        ordersTable.orderStatus == 2  # Adjust according to your business logic
    ).group_by(
        func.to_char(ordersTable.addedAt, 'YYYY-MM')
    ).order_by(
        func.to_char(ordersTable.addedAt, 'YYYY-MM')
    ).all()
    
        sales_dict = {month: total_sales for month, total_sales in sales_data}
        
        # Generate all months in the specified date range
        monthly_sales = []
        current_date = start_date

        while current_date <= end_date:
            month_key = current_date.strftime('%Y-%m')
            total_sales = sales_dict.get(month_key, 0)  # Default to 0 if no sales
            monthly_sales.append({
                "month": month_name[current_date.month],  # Get month name
                "total_sales": total_sales
            })
            current_date += relativedelta(months=1)  # Move to the next month

        # Output the result
        detail = {
            "Cancelled": result.cancelled or 0,
            "Pending": result.pending or 0,
            "Ongoing": result.dispatched or 0,
            "Totalsale": result.sales or 0,
            "MerchantGraph": jsonable_encoder(monthly_sales),
        }
        return JSONResponse(status_code=200, content={"detail": detail})
    
    except Exception as e:
        db.rollback()
        print(e)  # Consider logging this instead of printing
        return JSONResponse(status_code=500, content={"detail": "An error occurred"})
    

@router.post("/view-earnings", tags=["Merchant"])
async def viewEarnings(dm:datemo,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    merchantIds = decoded_token.get('merchantIds')
    if userType != "merchant":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"}) 
    
    # getmerchant = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
    if int(dm.merchantId) not in merchantIds:
        return JSONResponse(status_code=403, content={"detail": "you do not have access to this account"})
   

    year, month = map(int, dm.yearMonth.split('-'))
    first_day = date(year, month, 1)
    last_day = (first_day.replace(month=month % 12 + 1, day=1) - timedelta(days=1)) if month < 12 else date(year + 1, 1, 1) - timedelta(days=1)
    
    days_list = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]

    # Query to get daily earnings for the specified month and year
    daily_earnings_query = (
        select(
            func.date( ordersTable.addedAt).label('date'), #'day',_trunc
            func.sum(ordersTable.totalAmount).label('total_earnings')
        )
        .filter(
            ordersTable.orderStatus == 2,
            ordersTable.status == 0,
            ordersTable.merchantId == int(dm.merchantId),
            func.extract('year', ordersTable.addedAt) == year,
            func.extract('month', ordersTable.addedAt) == month
        )
        .group_by(func.date(ordersTable.addedAt))
    )

    # Execute the query and fetch results
    daily_earnings = db.execute(daily_earnings_query).fetchall()
    # print("Raw daily earnings:", daily_earnings)

    # Create a dictionary for easy lookup
    earnings_dict = {row.date: row.total_earnings for row in daily_earnings}

    # Prepare the result with all days, defaulting to 0 if no earnings
    result = [{"date": str(day), "total_earnings": earnings_dict.get(day, 0)} for day in days_list]
    
    return JSONResponse(status_code=200, content={"detail":jsonable_encoder(result)})


@router.post('/merchant-signup',tags=['Merchant'])
async def merchantSignup(su:signupModel, db:db_dependency):

    getuserName = db.query(users.userName).filter(users.userName == su.userName).scalar()
    if getuserName is not None:
        return JSONResponse(status_code=406, content={"detail":"user exists with this username"})
    getuserEmail = db.query(users.userEmail).filter(users.userEmail == su.userEmail).scalar()
    if getuserEmail is not None:
        return JSONResponse(status_code=406, content={"detail":"user exists with this email"})

    referralCode = uuid.uuid4().hex[:10]
    password = hash_password(su.password)
    try:
        db_user = users(userName=su.userName,userEmail=su.userEmail,userPhone=su.userPhone, password=password, userType=2, referralCode=referralCode)
        db.add(db_user)
        
        db.commit()
        db.flush()
        access_token = create_access_token(
        data={"userName": su.userEmail, "userId": db_user.userId, "userType": "merchant"}
        )
        return JSONResponse(status_code=200, content={"detail":"user added successfully","accessToken":access_token,"userType":2})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"detail":"Failed to create merchant"})
    

@router.post("/merchant-newstore", tags=["Merchant"])
async def merchantStorecreation(mm:merchantonboarding,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    userEmail = decoded_token.get('userName')
    if userType != "merchant":
        return JSONResponse(status_code=403, content={"detail": "you lack merchant privilages"})
    try:
      
        db_subext = merchantTable(address=mm.address,displayAddress=mm.displayAddress,phoneNumber=mm.phoneNumber,shopName=mm.shopName,shopEmail=mm.shopEmail,coverImage=mm.coverImage,handledByUser=userId,description=mm.description,servingRadius=mm.servingRadius,longitude=mm.longitude,latitude=mm.latitude,openingTime=mm.openingTime,closingTime=mm.closingTime)

        db.add(db_subext)
        db.flush()
        if len(mm.tags) > 0:
            for tag in mm.tags:
                addTag = searchTable(merchantId=db_subext.merchantId,searchTag=tag)
                db.add(addTag)
        db.commit()
        getmerchantIds = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).all()
        merchant_ids = [merchant[0] for merchant in getmerchantIds]
        access_token = create_access_token(
        data={"userName": userEmail, "userId": userId,"merchantIds": merchant_ids, "userType":userType}
        )
        return JSONResponse(status_code=200 , content={"detail":"Onboarding Complete","newToken":access_token})

    except Exception as e:
        db.rollback()
       
        print(e)
        return JSONResponse(status_code=500, content={"detail":"failed to add details"})
    

@router.get("/merchant-viewstores", tags=["Merchant"])
async def merchantviewStores(db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    userEmail = decoded_token.get('userName')
    if userType != "merchant":
        return JSONResponse(status_code=403, content={"detail": "you lack merchant privilages"})
    try:
      
        fetch = db.query(merchantTable).filter(merchantTable.handledByUser == userId).all()
        if fetch is None:
            return JSONResponse(status_code=200 , content={"detail":[],"message":"no store found tap to create a new store"})
        
        return JSONResponse(status_code=200 , content={"detail":jsonable_encoder(fetch)})

    except Exception as e:
        db.rollback()
       
        print(e)
        return JSONResponse(status_code=500, content={"detail":[], "message":"error"})
    


@router.post("/merchant-edit-merchant", tags=["Merchant"])
async def editMerchant(mm:merchantEditMerchant,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)): 
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    
    if userType != "merchant":
        
        return JSONResponse(status_code=403, content={"detail": "you lack privilages"})

    merchantId = int(mm.merchantId)
    merchantIds = decoded_token.get('merchantIds')
    
    if merchantId not in merchantIds:
        return JSONResponse(status_code=403, content={"detail": "you do not have access to this account"})

    try:
        
        getmerchant = db.query(merchantTable).filter(merchantTable.merchantId == merchantId).first()
        if getmerchant is None:
            return JSONResponse(status_code=404 , content={"detail":"merchant not found"})


       
        if mm.address != "":
            getmerchant.address = mm.address
        if mm.shopEmail != "":
            getmerchant.shopEmail = mm.shopEmail
        if mm.shopName != "":
            getmerchant.shopName = mm.shopName
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
        if mm.shopStatus != "":
            getmerchant.shopStatus = int(mm.shopStatus)


        db.commit()

        return JSONResponse(status_code=200 , content={"detail":"updated successfully"})

    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":"failed to update"})