from fastapi import APIRouter, Depends
from base_model import assignOrderModel, deliveryboyAvailability, acceptOrderModel, chooseshiftmodel, deliveredModel, userLoc, datemo, signupModel, userProfileModel
from database import db_dependency
from routes.token import decode_token, bearer_scheme,create_access_token, hash_password
from typing import Optional
from fastapi.responses import JSONResponse
from models import orderDeliveryModel,users, ordersTable, deliveryAgentLog, merchantTable, incentiveStructureModel, deliveryIncentiveModel, orderSettingsModel
from sqlalchemy.orm import joinedload
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select, and_, or_
from routes.helpers import distanceCalculate, haversine, reverseGeocode
from datetime import datetime, timedelta, date
import math
from routes.chat import send_message_fun
import uuid
# from routes.order import deliveryChargePerKm


router = APIRouter()

@router.post("/assign-order", tags=["deliveryAgent"])
async def assignOrder(ao:assignOrderModel,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin" and userType != "manager":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    
    try:
        checkOrderStatus = db.query(ordersTable).filter(ordersTable.orderId == ao.orderId).first()
        if checkOrderStatus.orderStatus is None:
            return JSONResponse(status_code=404, content={"detail": "order not found"})
        if checkOrderStatus == 3:
            return JSONResponse(status_code=406, content={"detail": "you cannot assign this order because the merchant havent accepted it"})

        #assigninng a delivery agent manually
        if ao.modeOfAssigning == 0:

            deliveryAgent = ao.deliveryAgent
        #assigning closest delivery agent automatically using haversine 
        if ao.modeOfAssigning == 1:

            getcoordinates = db.query(merchantTable).filter(merchantTable.merchantId == int(ao.merchantId)).first()
            if getcoordinates is None:
                return JSONResponse(status_code=404, content={"detail": "merchant not found"})
            longitude = float(getcoordinates.longitude)
            latitude = float(getcoordinates.latitude)
            radius = 90  # Define a radius in kilometers

    # Calculate bounding box for latitude and longitude
            lat_range = (latitude - (radius / 111), latitude + (radius / 111))  # Roughly 1 degree latitude = 111 km
            lon_range = (longitude - (radius / (111 * math.cos(math.radians(latitude)))), 
                        longitude + (radius / (111 * math.cos(math.radians(latitude)))))
           
            currentDay = datetime.now().date()
            #print(currentDay)
            # Fetch delivery agents within the bounding box
            fetch = db.query(deliveryAgentLog).filter(deliveryAgentLog.logDate == currentDay,deliveryAgentLog.isActive == 1,deliveryAgentLog.latitude.between(lat_range[0], lat_range[1]),deliveryAgentLog.longitude.between(lon_range[0], lon_range[1])).all()
           
            # Calculate distances and filter
            closest_agents = []
            for agent in fetch:
                agent_latitude = float(agent.latitude)  # Ensure it's treated as float
                agent_longitude = float(agent.longitude)  # Ensure it's treated as float
                distance = haversine(latitude, longitude, agent_latitude, agent_longitude)
                closest_agents.append((agent, distance))
            # Check if we have any closest agents
            if not closest_agents:
                return JSONResponse(status_code=404, content={"detail": "No delivery agents found within the specified radius."})
            #Sort and limit as before
            closest_agents.sort(key=lambda x: x[1])
            closest_agents = closest_agents[:1]
            deliveryAgent = closest_agents[0][0].userId
            
            # response_data = [agent[0] for agent in closest_agents]
            # return JSONResponse(status_code=200, content={"detail": jsonable_encoder(closest_agents[0][0].userId)})
        
        earning = db.query(orderSettingsModel.earningForAgent).scalar()
        earningForAgent = earning * checkOrderStatus.distanceFromMerchant
        if ao.deliveryAgentEarning != "":
            earningForAgent = float(ao.deliveryAgentEarning)
        fetch = db.query(orderDeliveryModel).filter(orderDeliveryModel.orderId == ao.orderId).first()
        if fetch is None:
            
            assign = orderDeliveryModel(deliveryAgentId = deliveryAgent,orderId = ao.orderId, earningForDeliveryAgent= earningForAgent)

            db.add(assign)

        else:
            fetch.deliveryAgentId = deliveryAgent
            fetch.earningForDeliveryAgent = earningForAgent
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "order assigned","deliveryAgent":deliveryAgent})
    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":"unable to assign order"})


#if u give a particular merchant id the api will give the 5 delivery agents that are closest to the merchant
#if there is no merchant id the api will list the delivery agents filter active and inactive according to admin requirement

@router.post("/list-deliveryagents", tags=["deliveryAgent"])
async def listDeliveryBoys(da:deliveryboyAvailability, db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    limit = int(da.limit) if da.limit else 10
    page = int(da.page) if da.page else 1
    offset = limit * (page - 1)
    if userType != "admin":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
  
    try:
       
        if da.merchantId != "":
            getcoordinates = db.query(merchantTable).filter(merchantTable.merchantId == int(da.merchantId)).first()
            if getcoordinates is None:
                return JSONResponse(status_code=404, content={"detail": "merchant not found"})
            longitude = float(getcoordinates.longitude)
            latitude = float(getcoordinates.latitude)
            radius = 50  # Define a radius in kilometers

    # Calculate bounding box for latitude and longitude
            lat_range = (latitude - (radius / 111), latitude + (radius / 111))  # Roughly 1 degree latitude = 111 km
            lon_range = (longitude - (radius / (111 * math.cos(math.radians(latitude)))), 
                        longitude + (radius / (111 * math.cos(math.radians(latitude))) ))
           
            
            # Fetch delivery agents within the bounding box
            fetch = db.query(deliveryAgentLog).filter(deliveryAgentLog.logDate == da.day,deliveryAgentLog.isActive == 1,deliveryAgentLog.latitude.between(lat_range[0], lat_range[1]),deliveryAgentLog.longitude.between(lon_range[0], lon_range[1])).all()
           
            # Calculate distances and filter
            closest_agents = []
            for agent in fetch:
                agent_latitude = float(agent.latitude)  # Ensure it's treated as float
                agent_longitude = float(agent.longitude)  # Ensure it's treated as float
                distance = haversine(latitude, longitude, agent_latitude, agent_longitude)
                closest_agents.append((agent, distance))

            #Sort and limit as before
            closest_agents.sort(key=lambda x: x[1])
            closest_agents = closest_agents[:limit]

            response_data = [agent[0] for agent in closest_agents]
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(closest_agents)})

        fetch = db.query(deliveryAgentLog).options(joinedload(deliveryAgentLog.deliveryagentloguser).joinedload(users.userdeliveryagentpersonal)).filter(deliveryAgentLog.logDate == da.day)
        
        if da.isActive != "":
            fetch = fetch.filter(deliveryAgentLog.isActive == int(da.isActive))

        fetch = fetch.order_by(deliveryAgentLog.logDate.desc()).limit(limit).offset(offset).all()   

        if fetch is None:
            return JSONResponse(status_code=200, content={"detail": []})
        else:
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(fetch)})

    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":[]})
    
#show distance duration and earning for the delivery agent before picking order

@router.post("/show-distance-oforder", tags=["deliveryAgent"])
async def showDistanceOfOrder(am:acceptOrderModel,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack delivery agent privilages"})

    try:
        accept = db.query(orderDeliveryModel).filter(orderDeliveryModel.orderId == am.orderId, orderDeliveryModel.deliveryAgentId == userId).first()   #orderDeliveryModel(orderId=am.orderId, deliveryAgentId= userId, orderAccepted= 1)
        if accept is None:
            return JSONResponse(status_code=404, content={"detail": {},"message":"order data not found"})
        getordertabledata = db.query(ordersTable).filter(ordersTable.orderId == am.orderId).first()
        if getordertabledata is None:
            return JSONResponse(status_code=404, content={"detail": {},"message": "order not found"})
        
        merchantcoordinates = db.query(merchantTable).options(joinedload(merchantTable.merchantImage)).filter(merchantTable.merchantId == getordertabledata.merchantId).first()
        if merchantcoordinates is None:
            return JSONResponse(status_code=404, content={"detail": {},"message": "merchant location not found"})
        
        getdistancetomerchant = await distanceCalculate(float(am.latitude),float(am.longitude),merchantcoordinates.latitude,merchantcoordinates.longitude)
        merchantstatus = getdistancetomerchant['status']
       

        if merchantstatus != "SUCCESS":
            return JSONResponse(status_code=404, content={"detail":{},"message":"unable to calculate distance to merchant"})
        
        merchantdistance = getdistancetomerchant['rows'][0]['elements'][0]['distance']
        merchantduration = getdistancetomerchant['rows'][0]['elements'][0]['duration']
        merchantdistanceInKm = round(merchantdistance / 1000, 2)
        merchantdurationInMin = round(merchantduration / 60, 2)

        getdistancetocustomer = await distanceCalculate(merchantcoordinates.latitude, merchantcoordinates.longitude,getordertabledata.latitude,getordertabledata.longitude)
        customerstatus = getdistancetocustomer['status']
        

        if customerstatus != "SUCCESS":
            return JSONResponse(status_code=404, content={"detail":{},"message":"unable to calculate distance to customer"})
        
        customerdistance = getdistancetocustomer['rows'][0]['elements'][0]['distance']
        customerduration = getdistancetocustomer['rows'][0]['elements'][0]['duration']
        customerdistanceInKm = round(customerdistance / 1000, 2)
        customerdurationInMin = round(customerduration / 60, 2)

        totaldistance = merchantdistanceInKm + customerdistanceInKm
        totalduration = merchantdurationInMin + customerdurationInMin

        # userAddressFromCoordinates = await reverseGeocode(getordertabledata.latitude,getordertabledata.longitude)
        
        userData = db.query(users).options(joinedload(users.userrelation2)).filter(users.userId == getordertabledata.userId).first()
        
        alldata = {
            "earningForAgent": accept.earningForDeliveryAgent if accept.earningForDeliveryAgent else 0,
            "merchantData": jsonable_encoder(merchantcoordinates),
            "userData": jsonable_encoder(userData),
            "customerAddress": getordertabledata.orderedAddress,
            "merchantdistance":merchantdistanceInKm if merchantdistanceInKm else 0,
            "merchantduration": merchantdurationInMin if merchantdurationInMin else 0,
            "customerdistance": customerdistanceInKm if customerdistanceInKm else 0,
            "customerduration": customerdurationInMin if customerdurationInMin else 0,
            "totaldistance":  totaldistance if  totaldistance else 0,
            "totalduration": totalduration if totalduration else 0
        }

        return JSONResponse(status_code=200, content={"alldata": alldata})
    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":{}})

    

@router.post("/accept-order", tags=["deliveryAgent"])
async def acceptOrder(am:acceptOrderModel,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack delivery agent privilages"})
    
    try:
        accept = db.query(orderDeliveryModel).filter(orderDeliveryModel.orderId == am.orderId, orderDeliveryModel.deliveryAgentId == userId).first()   #orderDeliveryModel(orderId=am.orderId, deliveryAgentId= userId, orderAccepted= 1)
        if accept is None:
            return JSONResponse(status_code=404, content={"detail": "order data not found"})
        getordertabledata = db.query(ordersTable).filter(ordersTable.orderId == am.orderId).first()
        if getordertabledata is None:
            return JSONResponse(status_code=404, content={"detail": "order not found"})
        
        # merchantCoordinates = db.query(merchantTable).filter(merchantTable.merchantId == getordertabledata.merchantId).first()
        # if merchantCoordinates is None:
        #     return JSONResponse(status_code=403, content={"detail": "merchant not found"})
        

        # getalldata = await distanceCalculate(am.latitude, am.longitude, merchantCoordinates.latitude, merchantCoordinates.longitude)   

        # mapstatus = getalldata['status']
        # if mapstatus != "SUCCESS":
        #     return JSONResponse(status_code=404, content={"detail": "unable to calculate distance to your current location"})
        # distance = getalldata['rows'][0]['elements'][0]['distance']
        # duration = getalldata['rows'][0]['elements'][0]['duration']

        
        

        # distanceInKm = round(distance / 1000, 2)
        # durationInMin = round(duration / 60, 2)
       
        
        getordertabledata.deliveryAgentId = userId
        accept.orderAccepted = 1
        #db.add(accept)
        db.commit()
        message = ({'message': "order assigned",'orderId': am.orderId, 'userId':userId})
        
        # await send_message_fun(db,message,userId,merchantUserId,0,om.merchantId,addorder.orderId)
        await send_message_fun(db,message,userId,getordertabledata.userId,0,0,am.orderId)
        return JSONResponse(status_code=200, content={"detail": "order accepted"})
    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":"error in accepting order"})


    



@router.put("/picked-from-merchant/{orderId}", tags=["deliveryAgent"])
async def pickedFromMerchant(orderId:int,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack delivery agent privilages"})
    try:
        verifyAgent = db.query(orderDeliveryModel).filter(orderDeliveryModel.orderId == orderId, orderDeliveryModel.orderAccepted == 1).first()
        if verifyAgent is None:
            return JSONResponse(status_code=404, content={"detail": "order not accepted by any rider"})
        
        if verifyAgent.deliveryAgentId != userId:
            return JSONResponse(status_code=404, content={"detail": "this order is assigned for another agent"})
        
        fetch = db.query(ordersTable).filter(ordersTable.orderId == orderId).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail": "order not found"})
        #orderedUser = fetch.userId
        if fetch.orderStatus == 1:
            return JSONResponse(status_code=406, content={"detail": "order already picked up by driver"})
        
        if fetch.status == 1:
            return JSONResponse(status_code=406, content={"detail": "order cancelled"})
        
        fetch.orderStatus = 1
        db.commit()
        message = ({'message': f"order assigned",'orderId': orderId, 'userId':userId})
        
        await send_message_fun(db,message,userId,fetch.userId,0,0,orderId)
        # await send_message_fun(db,f"order {orderId} picked from merchant",userId,fetch.userId,2)
        return JSONResponse(status_code=200, content={"detail": "successfully picked order from merchant"})
    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":"error"})


@router.post("/choose-shift", tags=["deliveryAgent"])
async def chooseShift(cm:chooseshiftmodel, db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack delivery agent privilages"})
    try:
        checkifshiftchosen = db.query(deliveryAgentLog).filter(deliveryAgentLog.userId == userId, deliveryAgentLog.logDate == cm.shiftdate).first()
        if checkifshiftchosen is not None:
            return JSONResponse(status_code=406, content={"detail": "you already chosen a shift for this day"})
        addshift = deliveryAgentLog(userId=userId,shiftId= cm.shiftId, logDate= cm.shiftdate)
        db.add(addshift)
        db.commit()
        
        return JSONResponse(status_code=200, content={"detail": "shift chosen successfully"})

    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":"error"})
    

@router.post("/gave-to-customer", tags=["deliveryAgent"])
async def gaveToCustomer(dm:deliveredModel, db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    # print (decoded_token)
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack delivery agent privilages"})
    
    try:
    
        checkDeliveryAgent = db.query(orderDeliveryModel).filter(orderDeliveryModel.orderId == int(dm.orderId)).first()
        if checkDeliveryAgent is None:
            return JSONResponse(status_code=404, content={"detail": "order not found"})
        
        if checkDeliveryAgent.deliveryAgentId != userId:
            return JSONResponse(status_code=406, content={"detail": "the order is not meant for you"})
        
        checkOtp = db.query(ordersTable).filter(ordersTable.orderId == int(dm.orderId)).first()
        if checkOtp is None:
            return JSONResponse(status_code=404, content={"detail": "otp not found"})
        
        if checkOtp.orderOtp != int(dm.otp):
            return JSONResponse(status_code=406, content={"detail": "incorrect otp"})
        else:
            checkOtp.orderStatus = 2
            checkDeliveryAgent.reachedAt = datetime.now()

            thisday = datetime.now()
            today = thisday.date()
            start_of_week = thisday - timedelta(days=today.weekday())
            
            getEarningForDay = db.query(func.sum(orderDeliveryModel.earningForDeliveryAgent)).filter(func.date(orderDeliveryModel.addedAt) == today, orderDeliveryModel.deliveryAgentId == userId).scalar() or 0
            
            getEarningForWeek = db.query(func.sum(orderDeliveryModel.earningForDeliveryAgent)).filter(
            and_(
                orderDeliveryModel.addedAt >= start_of_week,orderDeliveryModel.addedAt <= thisday,orderDeliveryModel.deliveryAgentId == userId
            )
            ).scalar() or 0
           
            getEarningForMonth = db.query(func.sum(orderDeliveryModel.earningForDeliveryAgent)).filter(
                and_(
                    func.extract("month",orderDeliveryModel.addedAt) == thisday.month, orderDeliveryModel.deliveryAgentId == userId
                )
            ).scalar() or 0
            incentives = db.query(incentiveStructureModel).filter(
            or_(
                and_(incentiveStructureModel.type == 1, getEarningForDay >= incentiveStructureModel.earning),
                and_(incentiveStructureModel.type == 2, getEarningForWeek >= incentiveStructureModel.earning),
                and_(incentiveStructureModel.type == 3, getEarningForMonth >= incentiveStructureModel.earning)
            )
            ).all()
            max_earnings = {}
            for incentive in incentives:
                incentive_type = incentive.type 
                earning = incentive.amountLimit 
                
                # If this type is not in the dictionary or the earning is greater, update it
                if incentive_type not in max_earnings or earning > max_earnings[incentive_type]["earning"]:
                    max_earnings[incentive_type] =  {"incentiveId": incentive.incentiveId, "type": incentive_type, "earning": earning}

            for incentive_type, incentive_info in max_earnings.items():
                if incentive_type == 1:  # Daily
                    incentive_date = today
                    checkEntry = db.query(deliveryIncentiveModel).filter(func.date(deliveryIncentiveModel.dateOfIncentive) == incentive_date.date(), deliveryIncentiveModel.typeOfIncentive == 1).first()
                    
                elif incentive_type == 2:  # Weekly
                    incentive_date = thisday - timedelta(days=thisday.weekday())  # Start of the week (Monday)
                    checkEntry =  db.query(deliveryIncentiveModel).filter(func.date(deliveryIncentiveModel.dateOfIncentive) == incentive_date.date(), deliveryIncentiveModel.typeOfIncentive == 2).first()
                   

                elif incentive_type == 3:  # Monthly
                    incentive_date = datetime(today.year, today.month, 1)
                    checkEntry =  db.query(deliveryIncentiveModel).filter(func.date(deliveryIncentiveModel.dateOfIncentive) == incentive_date.date(), deliveryIncentiveModel.typeOfIncentive == 3).first()

                if checkEntry is None:    
                    new_incentive = deliveryIncentiveModel(deliveryAgentId=userId,typeOfIncentive=incentive_info["type"],amount=incentive_info["earning"],dateOfIncentive=incentive_date)  # Or use the appropriate date for weekly/monthly
                    db.add(new_incentive)
                else:
                    checkEntry.amount = incentive_info["earning"]
                

            db.commit()
            
            #,"incentives": [{"incentiveId": inc.incentiveId, "type": inc.type, "earning": inc.amountLimit} for inc in incentives]}
            # await send_message_fun(db,f"order {dm.orderId} completed",userId,checkOtp.userId,3)
            message = ({'message': f"order assigned",'orderId': dm.orderId, 'userId':userId})
        
            await send_message_fun(db,message,userId,checkOtp.userId,0,0,dm.orderId)
            return JSONResponse(status_code=200, content={"detail": "order complete"})
        
    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":"unable to process order"})
    

@router.post("/goactive", tags=["deliveryAgent"])
async def goactive(ul:userLoc,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack delivery agent privilages"})
    
    try:
        currentTime = datetime.now()
        # formatted_time = currentTime.strftime("%H:%M:%S")
        current_day = datetime.now().date()
        checkdaystatus = db.query(deliveryAgentLog).filter(deliveryAgentLog.logDate == current_day, deliveryAgentLog.userId == userId).first()

        if checkdaystatus is None:
            activate = deliveryAgentLog(userId=userId, startTime=currentTime, isActive=1, logDate=current_day, longitude= ul.longitude, latitude= ul.latitude)
            db.add(activate)
            message = "successfully activated"
        else:
            # Toggle the active state
            if checkdaystatus.isActive == 1:
                # If currently active, set end time and mark inactive
                checkdaystatus.endTime = currentTime
                checkdaystatus.isActive = 0
                checkdaystatus.latitude = ul.latitude
                checkdaystatus.longitude = ul.latitude
                message = "Successfully deactivated"
            else:
                # If currently inactive, update start time and mark active
                checkdaystatus.startTime = currentTime  # Update to the new start time
                checkdaystatus.isActive = 1
                checkdaystatus.endTime = None  # Clear the end time since they are active now
                checkdaystatus.latitude = ul.latitude
                checkdaystatus.longitude = ul.latitude
                message = "Successfully activated"
            


        db.commit()
        return JSONResponse(status_code=200, content={"detail": message})
    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":"unable to change status"})


@router.post("/send-coordinates", tags=["deliveryAgent"])
async def goactive(ul:userLoc,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack delivery agent privilages"})
    
    try:
        current_day = datetime.now().date()
        currentTime = datetime.now()
        getcurrentday =  db.query(deliveryAgentLog).filter(deliveryAgentLog.logDate == current_day, deliveryAgentLog.userId == userId).first()
        if getcurrentday is None:
            # return JSONResponse(status_code=404, content={"detail":"delivery data not found"})
            insert = deliveryAgentLog(logDate=current_day,userId=userId,latitude=ul.latitude,longitude=ul.longitude,last_update=currentTime)
            db.add(insert)
        else:
            getcurrentday.latitude = ul.latitude
            getcurrentday.longitude = ul.longitude
            getcurrentday.last_update = currentTime

        db.commit()
        return JSONResponse(status_code=200, content={"detail":"coordinates added"})

    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":"unable to send coordinates"})
    

@router.post("/agent-viewearnings", tags=["deliveryAgent"])
async def agentViewEarnings(dm:datemo,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"}) 
    
    
    year, month = map(int, dm.yearMonth.split('-'))
    first_day = date(year, month, 1)
    last_day = (first_day.replace(month=month % 12 + 1, day=1) - timedelta(days=1)) if month < 12 else date(year + 1, 1, 1) - timedelta(days=1)
    
    days_list = [first_day + timedelta(days=i) for i in range((last_day - first_day).days + 1)]

    # Query to get daily earnings for the specified month and year
    daily_earnings_query = (
        select(
            func.date( orderDeliveryModel.addedAt).label('date'), #'day',_trunc
            func.sum(orderDeliveryModel.earningForDeliveryAgent).label('total_earnings')
        )
        .filter(
            orderDeliveryModel.orderAccepted == 1,
            orderDeliveryModel.deliveryAgentId == userId,
            func.extract('year', orderDeliveryModel.addedAt) == year,
            func.extract('month', orderDeliveryModel.addedAt) == month
        )
        .group_by(func.date(orderDeliveryModel.addedAt))
    )

    # Execute the query and fetch results
    daily_earnings = db.execute(daily_earnings_query).fetchall()
 

    # Create a dictionary for easy lookup
    earnings_dict = {row.date: row.total_earnings for row in daily_earnings}

    # Prepare the result with all days, defaulting to 0 if no earnings
    result = [{"date": str(day), "total_earnings": earnings_dict.get(day, 0)} for day in days_list]
    
    return JSONResponse(status_code=200, content={"detail":jsonable_encoder(result)})


@router.post("/agent-home", tags=["deliveryAgent"])
async def agentHome(dm:datemo,db:db_dependency,token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"}) 
    
    try:
        getcount = (select(
                    func.count(ordersTable.orderId).filter(ordersTable.deliveryAgentId == userId, ordersTable.status == 1).label("cancelledOrders"),
                    func.count(ordersTable.orderId).filter(ordersTable.deliveryAgentId == userId, ordersTable.orderStatus == 2).label("totalOrders")
                ))       
        
        result = db.execute(getcount).one()

        thisday = datetime.now()
        today = thisday.date()
        
        getEarningForDay = db.query(func.sum(orderDeliveryModel.earningForDeliveryAgent)).filter(func.date(orderDeliveryModel.addedAt) == today, orderDeliveryModel.deliveryAgentId == userId).scalar() or 0
      
        
        start_of_week = thisday - timedelta(days=today.weekday())  # Monday

        getEarningForWeek = db.query(func.sum(orderDeliveryModel.earningForDeliveryAgent)).filter(
        and_(
            orderDeliveryModel.addedAt >= start_of_week,orderDeliveryModel.addedAt <= thisday,orderDeliveryModel.deliveryAgentId == userId
        )
        ).scalar() or 0
        
        getEarningForMonth = db.query(func.sum(orderDeliveryModel.earningForDeliveryAgent)).filter(
            and_(
                func.extract("month",orderDeliveryModel.addedAt) == thisday.month, orderDeliveryModel.deliveryAgentId == userId
            )
        ).scalar() or 0
        incentives = db.query(incentiveStructureModel).filter(
        or_(
            and_(incentiveStructureModel.type == 1, getEarningForDay >= incentiveStructureModel.earning),
            and_(incentiveStructureModel.type == 2, getEarningForWeek >= incentiveStructureModel.earning),
            and_(incentiveStructureModel.type == 3, getEarningForMonth >= incentiveStructureModel.earning)
        )
        ).all()
        #myincentive = [{"incentiveId": inc.incentiveId, "type": inc.type, "earning": inc.amountLimit} for inc in incentives]
        max_earnings = {}
      
        # Loop through the incentives
        for incentive in incentives:
            incentive_type = incentive.type 
            earning = incentive.amountLimit 
            
            # If this type is not in the dictionary or the earning is greater, update it
            if incentive_type not in max_earnings or earning > max_earnings[incentive_type]["earning"]:
                max_earnings[incentive_type] =  {"incentiveId": incentive.incentiveId, "type": incentive_type, "earning": earning}

        # Extract the values from the dictionary
        greatest_earnings = list(max_earnings.values())
        getall = {
                "cancelledOrders":result.cancelledOrders if result.cancelledOrders else 0,
                "totalOrders": result.totalOrders if result.totalOrders else 0,
                "incentiveGraph": greatest_earnings
        }

        return JSONResponse(status_code=200, content={"detail": getall})
    except Exception as e:
        db.rollback()
        print(e)
        return JSONResponse(status_code=500, content={"detail":{}})
    

@router.post("/delivery-signup" , summary="Signup API", tags=["Authentication"])
async def agent(db: db_dependency, su:signupModel):
    
    getuserName = db.query(users.userName).filter(users.userName == su.userName).scalar()
    if getuserName is not None:
        return JSONResponse(status_code=406, content={"detail":"user exists with this username"})
    getuserEmail = db.query(users.userEmail).filter(users.userEmail == su.userEmail).scalar()
    if getuserEmail is not None:
        return JSONResponse(status_code=406, content={"detail":"user exists with this email"})

    referralCode = uuid.uuid4().hex[:10]
    password = hash_password(su.password)
    try:
        db_user = users(userName=su.userName,userEmail=su.userEmail,userPhone=su.userPhone, password=password, userType=1,referralCode=referralCode)
        db.add(db_user)
        
        db.commit()
        db.flush()
        access_token = create_access_token(
        data={"userName": su.userEmail, "userId": db_user.userId, "userType": "deliveryAgent"}
        )
        return JSONResponse(status_code=200, content={"detail":"user added successfully","accessToken":access_token,"userType":1})
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"detail":"Failed to create delivery agent"})
    


@router.post("/view-deliveryagent", tags=["Admin"])
async def viewDeliveryAgent(u:userProfileModel,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "admin" and userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack admin privilages"})
    try:
        if userType == "admin":
            if u.userId != "":
                userId = int(u.userId)
        
        fetch = db.query(users).options(joinedload(users.userdeliveryagentpersonal)).filter(users.userId == userId).first()

        if fetch is None:
            return JSONResponse(status_code=200, content={"detail": []})
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(fetch)})

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"detail":[]})