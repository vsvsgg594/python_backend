import string
import random
from fastapi import APIRouter,UploadFile, File,Depends
from fastapi.responses import JSONResponse
from routes.token import decode_token, bearer_scheme
from routes.s3Bucket import s3Upload
from typing import Optional
from database import db_dependency
import uuid
import os
from models import productGallery,setSchedule, PreferenceTable, ordersTable, orderSettingsModel,referralModel,deliverysettingTable
from fastapi.encoders import jsonable_encoder
from base_model import page
import httpx
import math
from shapely.geometry import Point, Polygon
from routes.chat import notify,sentPersonal,notifyperson
from sqlalchemy.orm import Session


router = APIRouter()



def generate_random_string(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

bucketLink = os.getenv('bucketLink')

@router.post("/upload-file",summary="add objects in S3", tags=["Gallery"])
async def upload_file( db: db_dependency, file: UploadFile = File(...), token: Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userId = decoded_token.get("userId")
    

    contents = await file.read()
    # size = len(contents)
    # if not 0 < size <= 5 * MB:
    #     return JSONResponse(status_code=406, content={"detail":"maximum allowed filesize is 5 MB"})
    
    
    try:
        
        # Generate a unique identifier
        unique_id = uuid.uuid4().hex

        # Extract file extension
       
        # Construct unique filename
        unique_filename = f"{unique_id}_{file.filename}"
    
        s3Upload(contents=contents, key= unique_filename)

        myimage = bucketLink + unique_filename
        #return{"myimage": myimage, "userId": uId}
        ufile = productGallery(imageName= myimage, imageAlt=file.filename, uploadedBy= userId)
        db.add(ufile)
        db.commit()
        return JSONResponse(status_code=200, content={"detail":"File uploaded successfully"})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"detail":"Failed to upload file"})
    
@router.post("/view-uploadfile",summary="view objects in S3", tags=["Gallery"])
async def viewUploadFile(p:page, db: db_dependency, token: Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userId = decoded_token.get('userId')
    limit = int(p.limit) if p.limit else 10
    page = int(p.page) if p.page else 1
    offset = limit * (page - 1)
    try:
        fetch = db.query(productGallery).filter(productGallery.uploadedBy == userId).limit(limit).offset(offset).all()

        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(fetch)})

    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"detail":[]})

OLA_API = os.getenv('OLA_API')

async def distanceCalculate(originLat, originLong, destinationLat, destinationLong):
    
    url = 'https://api.olamaps.io/routing/v1/distanceMatrix'
    params = {
        'origins': f"{originLat},{originLong}",
        'destinations': f"{destinationLat},{destinationLong}",
        'api_key': OLA_API
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            data = response.json()
            return data
        except httpx.HTTPStatusError as e:
            raise JSONResponse(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise JSONResponse(status_code=500, detail=str(e))
        

async def reverseGeocode(latitude,longitude):

    url = 'https://api.olamaps.io/places/v1/reverse-geocode' 

    params = {
        'latlng': f"{latitude},{longitude}",
        'api_key': OLA_API
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            data = response.json()
            return data['results'][0]['formatted_address']
        except httpx.HTTPStatusError as e:
            raise JSONResponse(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise JSONResponse(status_code=500, detail=str(e))
        

def haversine(lat1, lon1, lat2, lon2):
    r = 6371  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return r * c

def check_coordinate(latitude,longitude, geopoints):
    point = Point(longitude, latitude)  # Shapely uses (lon, lat)
    polygon_points = [(lon, lat) for lat, lon in geopoints]
    if polygon_points[0] != polygon_points[-1]:
        polygon_points.append(polygon_points[0])
    polygon = Polygon(polygon_points)
    # print("Checking Point:", point)  # Debug output
    # print("Polygon Points:", polygon_points)
    # print("Polygon Contains Point:", polygon.contains(point))  # Debug output
    return polygon.contains(point)


def populate_initial_data(db):
    # Check if the table is empty
    # if db.query(PreferenceTable).count() == 0:
    #     # Create initial authors
    #     insert =PreferenceTable(countryCode= "+91",currency= "INR", currencyFormatting= 0, timeZone = 0, timeFormat = 0, dateFormat= 0, onlineAndOfflineTax=0,productShare=0,shortenAddressOnMap=0,deliveryAddressConfirmation=0,aerialDistance=0,favoriteMerchants=0,autoRefund=0,pickupNotifications=0,orderReadyStatus=0,distanceUnit=0,showCommisionToMerchants=0,customerRating=0,hideCustomerDetailFromMerchant=0,showCustomerProfileToMerchant=0,showCurrencyToMerchant=0,showGeofenceToMerchant=0,servingRadius=0,showacceptOrrejectmerchants=0)
    if db.query(orderSettingsModel).count() == 0:
        insert = orderSettingsModel(autoAccept=0,orderAcceptanceTime=0,allowMerchantToEdit=0,allowManagerToEdit=0,allowCustomersToRate=0,agentOrderAcceptanceTime=0,earningForAgent=0,autoAssignAgent=0)
        db.add(insert)

    if db.query(referralModel).count() == 0:
        addreferral = referralModel(referralType=0)
        db.add(addreferral)

    if db.query(deliverysettingTable).count() == 0:
        adddelivery = deliverysettingTable(deliveryTime=20,chargePerKm=10)
        db.add(adddelivery)
    db.commit()
    


#merchant cancel order

async def merchantCancellation(jobid: int, db: db_dependency):
    print(f"Scheduled task executed {jobid}")
    try:
        fetch = db.query(setSchedule).filter(setSchedule.jobId == jobid).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail":"not found"})
        
        orderData = db.query(ordersTable).filter(ordersTable.orderId == fetch.orderId).first()
        if orderData is None:
            return JSONResponse(status_code=404, content={"detail":"order data not found"})
        if orderData.orderStatus == 3:
            orderData.status = 1
            usermessage = ({'message': 'merchant didnt accept you order','orderId': fetch.orderId, 'userId':""})
            await notifyperson(db,message,fetch.userId,0,fetch.orderId)
            # await notify("merchant didn't accept your order",1,orderData.userId)
            # usermessage = ({'message': 'merchant didnt accept you order','orderId': fetch.orderId, 'userId':""})
            # await notifyperson(db,message,fetch.userId,0,fetch.orderId)
            # await notify("order cancelled",1,orderData.merchantId)
            if orderData.paymentMethod == "0":
                message = ({'message': 'order cancelled please process refund','orderId': fetch.orderId, 'userId':orderData.userId})
                await notifyperson(db,message,1,0,fetch.orderId)
                # sentPersonal(f"order {fetch.orderId} got cancelled please process the refund asap")
        fetch.executionStatus = 0
            # if orderData.paymentMethod == "0":

        db.commit()
      
    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":"unable to cancel order"})



#delivery agent cancel order

def agentCancellation(jobid: int, db: Session):
    print(f"Scheduled task executed {jobid}")
    try:
        fetch = db.query(setSchedule).filter(setSchedule.jobId == jobid).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail":"not found"})
        
        orderData = db.query(ordersTable).filter(ordersTable.orderId == fetch.orderId).first()
        if orderData is None:
            return JSONResponse(status_code=404, content={"detail":"order data not found"})
        # if orderData.orderStatus == 3:
            #cancel order
        return
      
    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":""})