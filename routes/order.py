from fastapi import APIRouter,Depends, BackgroundTasks, Request
from database import db_dependency
from routes.authentication import bearer_scheme, decode_token
from typing import Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload
from fastapi.encoders import jsonable_encoder
from base_model import orderBase, orderpagination, orderPriceBase, editOrderModel
from models import *
import random
from routes.helpers import distanceCalculate,check_coordinate, merchantCancellation, haversine
from routes.emailOtp import generate_otp
from routes.chat import send_message_fun
from sqlalchemy import func
from datetime import timedelta
import pytz
from apscheduler.triggers.date import DateTrigger
from routes.chat import sentPersonal, notify,notifyperson
from routes.scheduler import scheduler
import math
import json
from routes.websocketConn import redis_client
REDIS_DELIVERY_CHARGE = 0
REDIS_GEOFENCE = "geofence_data"
router = APIRouter()
#manager = connectionManager()

# how to handle 
# referal
# multiple merchantid for same user
# shop closing and opening
# serving radius


@router.post("/order-price", tags=["Orders"], summary="start redis server by going to redis folder using cmd and typing redis-server.exe Use this api to show the user what will be the charges when he orders now. It will cache the current delivery charge and geofences.Then proceed to use place order API. Remember this api first !!")
async def orderPrice(om:orderPriceBase,db:db_dependency, request:Request, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType not in ["admin", "customer", "merchant"]:
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    
    try:
        

        getdelivery = db.query(deliverysettingTable.chargePerKm).scalar() 
        deliveryChargePerKm = getdelivery if getdelivery else 10    
        redis_client.set(REDIS_DELIVERY_CHARGE, deliveryChargePerKm) #caching delivery charge

        getgeofences = db.query(geofenceTable).filter(geofenceTable.isActive == 0, geofenceTable.status == 0).all()
        
        if not getgeofences:
            return JSONResponse(status_code=404, content={"detail": "geofence not found"})
        
        geodata = jsonable_encoder(getgeofences)
        geofences_bytes = json.dumps(geodata)
        redis_client.set(REDIS_GEOFENCE, geofences_bytes)  #caching the geofence
        # print(REDIS_GEOFENCE)
        # print("Stored value in Redis:", redis_client.get(REDIS_GEOFENCE))
        insideGeofence = False
        for geo in getgeofences:
             #print(geo.points)
             if check_coordinate(float(om.latitude), float(om.longitude), list(geo.points)):
                
                insideGeofence = True
                break
             
        if not insideGeofence:
            return JSONResponse(status_code=406, content={"detail": "sorry we dont deliver to your location"})
                
        merchantAvailability = db.query(merchantTable).filter(merchantTable.merchantId == om.merchantId).first()
        if merchantAvailability is None:
            return JSONResponse(status_code=404, content={"detail": "merchant not found"})
        if merchantAvailability.shopStatus == 1:
            return JSONResponse(status_code=404, content={"detail": "merchant not available"})
        if merchantAvailability.status == 1:
            getterminology = db.query(terminologyTable.terminology).filter(terminologyTable.type == 1, terminologyTable.subType == 2).scalar()

            return JSONResponse(status_code=204, content={"detail": getterminology if getterminology else "the merchant is not active currently"})
        
        currentTime = datetime.now().time()
        # if merchantAvailability.openingTime > currentTime:
        #     return JSONResponse(status_code=204, content={"detail": "merchant havent opened the shop yet please wait"})

        # if merchantAvailability.closingTime < currentTime:
        #     return JSONResponse(status_code=204, content={"detail": "merchant closed the shop for the day"})

        getofferprice = 0
        totalPrice = 0
        coupon = 0
        if om.couponCode != "":
            
            getcoupon = db.query(couponsTable).filter(couponsTable.code == om.couponCode).first()
            if getcoupon is None:
                return JSONResponse(status_code=404, content={"detail": "coupon not found"})
            coupon = getcoupon.couponId
             
            if getcoupon.startingdate > datetime.now():
                return JSONResponse(status_code=403, content={"detail": "coupon offer not started"})
            if getcoupon.endingdate < datetime.now():
                return JSONResponse(status_code=403, content={"detail": "coupon offer expired"})
            if getcoupon.UsersCount == 0:
                return JSONResponse(status_code=403, content={"detail": "coupon offer not available"})
            getcoupon.UsersCount += 1
            getofferprice = random.randint(0, getcoupon.maxValue)
            totalPrice -= getofferprice 

        # merchantCoordinates = db.query(merchantTable).filter(merchantTable.merchantId == om.merchantId).first()
        # if merchantCoordinates is None:
        #     return JSONResponse(status_code=403, content={"detail": "merchant not found"})
        

        getalldata = await distanceCalculate(om.latitude, om.longitude, merchantAvailability.latitude, merchantAvailability.longitude)   

        mapstatus = getalldata['status']
        if mapstatus != "SUCCESS":
            return JSONResponse(status_code=404, content={"detail": "unable to calculate distance to your current location"})
        # distance = getalldata['rows'][0]['elements'][0]['distance']
        # duration = getalldata['rows'][0]['elements'][0]['duration']

       
        

        distanceInKm = round(getalldata['rows'][0]['elements'][0]['distance'] / 1000, 2)
        durationInMin = round(getalldata['rows'][0]['elements'][0]['duration'] / 60, 2)
        deliveryCharge = round(distanceInKm * deliveryChargePerKm, 2)
        
        if distanceInKm > merchantAvailability.servingRadius:
            return JSONResponse(status_code=406, content={"detail": "this restaurant does not serve food that far"})
        showtaxes = []
        preparationTime = 0
        for i in om.order:
            getPrice = db.query(productsTable).filter(productsTable.productId == i.productId).first()
            totalProductPrice = getPrice.price * i.quantity
            productName = getPrice.productName
            getproductTax = db.query(productTaxTable).options(joinedload(productTaxTable.producttaxrelation)).filter(productTaxTable.productId == i.productId).all()
            tax_info = []
            if getproductTax is not None:
                for item in getproductTax:
                    
                    tax_name = item.producttaxrelation.taxName
                    
                    totalProductPrice += (i.quantity * item.taxAmount)
                    
                    tax_info.append({
                        "taxAmount": item.taxAmount,
                        "taxName": tax_name,
                        
                    })

            showtaxes.append({"productName":productName,"tax":tax_info})
            preparationTime += int(getPrice.preparationTime)
            totalPrice += totalProductPrice
           
        
        totalAmount = totalPrice

  
        totalAmount += deliveryCharge

        getDiscountOfMerchant = db.query(discountMerchantTable).options(joinedload(discountMerchantTable.discounttable)).filter(discountMerchantTable.merchantId == om.merchantId).first()
        if getDiscountOfMerchant is not None:
            minimumOrderAmount = getDiscountOfMerchant.discounttable.minimumOrderAmount
            if minimumOrderAmount <= totalAmount:
                dType = getDiscountOfMerchant.discounttable.discountType
                dValue = getDiscountOfMerchant.discounttable.maxiamt
                discountValue = getDiscountOfMerchant.discounttable.discountValue
                
                minusValue = 0
                if dType == 1:
                    minusValue = totalAmount * ((random.uniform(discountValue,dValue)) / 100)
                    #totalAmount -= minusValue
                else:
                    minusValue = random.uniform(discountValue,dValue)
                request.session['discountValue'] = minusValue     
                totalAmount -= minusValue
                getofferprice += minusValue
            else:
                request.session['discountValue'] = 0
        else:
            request.session['discountValue'] = 0

        # getreferalCode = db.query(users.referralCode).filter(users.userId == userId).scalar()
        # checkIfUserRedeemed = db.query(referalDiscount).filter(referalDiscount.referalCode == getreferalCode).first()
        # if checkIfUserRedeemed is not None:
        #     getMaxMinDiscount = db.query(referralModel).first()
            
        #     referalMinOrderAmount = getMaxMinDiscount.minimumOrderAmount
        #     referaldiscountType = getMaxMinDiscount.referralType
        #     referalMaxValue = getMaxMinDiscount.refereeMaximumDiscountValue 
        #     referalMinValue = getMaxMinDiscount.refereeDiscountPercentange
        #     if referalMinOrderAmount <= totalAmount:
        #         if referaldiscountType == 1:
        #             referalValue = totalAmount * ((random.uniform(referalMinValue,referalMaxValue)) / 100)
        #         else:
        #             referalValue = random.uniform(referalMinValue,referalMaxValue)

                # totalAmount -= referalValue
                # getofferprice += referalValue
    
        output = {"totalPrice": round(totalAmount, 2),
                  "valueReduced": getofferprice,
                  "taxes": showtaxes,
                  "productTotalIncludingTax": totalProductPrice,
                  "deliveryCharge": deliveryCharge,
                  "distance": distanceInKm,
                  "preparationTime": preparationTime,
                  "duration": durationInMin
                  }
     

        return JSONResponse(status_code=200, content={"detail": "all tax included","charges": output})
    except Exception as e:
        print(e)
        #db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to get order data"})
    

@router.post("/place-order", tags=["Orders"])
async def placeOrder(om:orderBase,db:db_dependency,request:Request, background_tasks: BackgroundTasks, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType not in ["admin", "customer", "merchant"]:
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    
    try:
        
        # getreferalCode = db.query(users.referralCode).filter(users.userId == userId).scalar()
        # checkIfUserRedeemed = db.query(referalDiscount).filter(referalDiscount.referalCode == getreferalCode).first()
        # if checkIfUserRedeemed is not None:
        #     getMaxMinDiscount = db.query(referralModel).first() 

        #getdelivery =  #db.query(deliverysettingTable.chargePerKm).scalar()
        deliveryChargePerKm = redis_client.get(REDIS_DELIVERY_CHARGE) #getdelivery if getdelivery else 10   
 
        geofences_data = redis_client.get(REDIS_GEOFENCE)#db.query(geofenceTable).filter(geofenceTable.isActive == 0, geofenceTable.status == 0).all()
        # print("Type of geofences_data:", type(geofences_data))
        # print(geofences_data)
        getgeofences = json.loads(geofences_data)
       
        if not getgeofences:
            return JSONResponse(status_code=404, content={"detail": "geofence not found"})
        
        
        insideGeofence = False
        for geo in getgeofences:
             #print(geo.points)
             if check_coordinate(float(om.latitude), float(om.longitude), list(geo['points'])):
                
                insideGeofence = True
                break
             
        if not insideGeofence:
            return JSONResponse(status_code=406, content={"detail": "sorry we dont deliver to your location"})
        

        merchantAvailability = db.query(merchantTable).filter(merchantTable.merchantId == om.merchantId).first()
        if merchantAvailability is None:
            return JSONResponse(status_code=404, content={"detail": "merchant not found"})
        if merchantAvailability.shopStatus == 1:
            return JSONResponse(status_code=404, content={"detail": "merchant not available"})
        if merchantAvailability.status == 1:
            getterminology = db.query(terminologyTable.terminology).filter(terminologyTable.type == 1, terminologyTable.subType == 2).scalar()
            return JSONResponse(status_code=200, content={"detail": getterminology if getterminology else "merchant is not active currently"}) # fetch the terminology from terminology table
        
        current = datetime.now()
        currentTime = current.time()
        # if merchantAvailability.openingTime > currentTime:
        #     return JSONResponse(status_code=200, content={"detail": "shop is not opened yet"})

        # if merchantAvailability.closingTime < currentTime:
        #     return JSONResponse(status_code=200, content={"detail": "shop is closed for the day"})
        
        
        
        getalldata = await distanceCalculate(om.latitude, om.longitude, merchantAvailability.latitude, merchantAvailability.longitude)   
        userAddressFromCoordinates = om.address #await reverseGeocode(om.latitude,om.longitude)

        mapstatus = getalldata['status']
        if mapstatus != "SUCCESS":
            return JSONResponse(status_code=404, content={"detail": "unable to calculate distance to your current location"})
        distance = round(getalldata['rows'][0]['elements'][0]['distance'] / 1000, 2)
        duration = round(getalldata['rows'][0]['elements'][0]['duration'] / 60, 2)

        if distance > merchantAvailability.servingRadius:
            return JSONResponse(status_code=406, content={"detail": "this restaurant does not serve food that far"})
        merchantUserId = merchantAvailability.handledByUser

        # distanceInKm = round(distance / 1000, 2)
        # durationInMin = round(duration / 60, 2)
        deliveryCharge = round(distance * float(deliveryChargePerKm), 2)
      
        amountToBeCollected = 0
        getofferprice = 0
        totalPrice = 0
        coupon = 0
        if om.couponCode != "":
            
            getcoupon = db.query(couponsTable).filter(couponsTable.code == om.couponCode).first()
            if getcoupon is None:
                return JSONResponse(status_code=404, content={"detail": "coupon not found"})
            coupon = getcoupon.couponId
             
            if getcoupon.startingdate > current:
                return JSONResponse(status_code=204, content={"detail": "coupon offer not started"})
            if getcoupon.endingdate < current:
                return JSONResponse(status_code=204, content={"detail": "coupon offer expired"})
            if getcoupon.UsersCount == 0:
                return JSONResponse(status_code=204, content={"detail": "coupon offer not available"})
            getcoupon.UsersCount += 1
            getofferprice = random.randint(0, getcoupon.maxValue)
            totalPrice -= getofferprice 
        
        earningForAgent = 0
        deliveryAgent = None
        myKey = "oradoKey"#uuid.uuid4().hex
        generatedOtp = generate_otp(myKey)
        myorderstatus = 0
        a=0
        getorderaccept = db.query(orderSettingsModel).first()  #getting earning for agent and order acceptance time
        if getorderaccept is not None:
            # if getorderaccept.agentOrderAcceptanceTime is not None:
            #     orderAcceptanceTime = getorderaccept.orderAcceptanceTime
            orderAcceptanceTime = (
                60 if getattr(getorderaccept, 'orderAcceptanceTime', 60) == 0
                else getattr(getorderaccept, 'orderAcceptanceTime', 60)
            )
            earningForAgent = getorderaccept.earningForAgent * distance
            if getorderaccept.autoAccept != "":
                if getorderaccept.autoAccept == 1:
                    myorderstatus = 3
            

                    if getorderaccept.autoAssignAgent == 1:

                        longitude = float(merchantAvailability.longitude)
                        latitude = float(merchantAvailability.latitude)
                        radius = 90  # Define a radius in kilometers

                # Calculate bounding box for latitude and longitude
                        lat_range = (latitude - (radius / 111), latitude + (radius / 111))  # Roughly 1 degree latitude = 111 km
                        lon_range = (longitude - (radius / (111 * math.cos(math.radians(latitude)))), 
                                    longitude + (radius / (111 * math.cos(math.radians(latitude)))))
                        
                        currentDay = current.date()
                    
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
                        if closest_agents:
                            
                            #Sort and limit as before
                            closest_agents.sort(key=lambda x: x[1])
                            closest_agents = closest_agents[:1]
                            deliveryAgent = closest_agents[0][0].userId
                        else:
                            a = 1
                    
        # addorder.deliveryAgentId = deliveryAgent
        addorder = ordersTable(userId= userId, merchantId= om.merchantId,deliveryInstruction= om.deliveryInstruction,valueReduced=getofferprice,durationFromMerchant=duration, merchantInstruction = om.merchantInstruction, tipAmount= om.tipAmount, deliveryMode= om.deliveryMode, paymentMethod= om.paymentMethod, latitude= om.latitude, longitude=om.longitude, orderOtp= generatedOtp, orderedAddress= userAddressFromCoordinates, orderStatus = myorderstatus)
        db.add(addorder)
        db.flush()

        if a == 1:
 
            message = ({'message': 'unable to find an agent for this order','orderId': addorder.orderId, 'userId':userId})
            await notifyperson(db,message,1,0,addorder.orderId)

        showtaxes = []
        preparationTime = 0
        for i in om.order:
            getPrice = db.query(productsTable).filter(productsTable.productId == i.productId).first()
            totalProductPrice = getPrice.price * i.quantity
            productName = getPrice.productName
            getproductTax = db.query(productTaxTable).options(joinedload(productTaxTable.producttaxrelation)).filter(productTaxTable.productId == i.productId).all()
            tax_info = []
            if getproductTax is not None:
                for item in getproductTax:
                    
                    tax_name = item.producttaxrelation.taxName
                    
                    totalProductPrice += (i.quantity * item.taxAmount)
                    
                    tax_info.append({
                        "taxAmount": item.taxAmount,
                        "taxName": tax_name,
                        
                    })
           
            showtaxes.append({"productName":productName,"tax":tax_info})
            preparationTime += float(getPrice.preparationTime)
            orderProducts = orderItemsTable(productId=i.productId, quantity= i.quantity, price= getPrice.price, productTotal= totalProductPrice, orderId= addorder.orderId)
            db.add(orderProducts)

            totalPrice += totalProductPrice
            
         
        totalAmount = totalPrice

  
        totalAmount += deliveryCharge
        totalAmount += om.tipAmount
        #paymentMethod 1 cash on delivery 0 is online payment
        if om.paymentMethod == "1":
            amountToBeCollected = totalAmount

        newTime = current + timedelta(minutes=duration) + timedelta(minutes=float(preparationTime))

        addToOrderDelivery = orderDeliveryModel(orderId = addorder.orderId, expectedArrival = newTime, distanceToTravel= distance, amountToBeCollected =amountToBeCollected, earningForDeliveryAgent = earningForAgent,deliveryAgentId=deliveryAgent)
        db.add(addToOrderDelivery)
      
        getDiscountOfMerchant = db.query(discountMerchantTable).options(joinedload(discountMerchantTable.discounttable)).filter(discountMerchantTable.merchantId == om.merchantId).first()
        if getDiscountOfMerchant is not None:
    
            minimumOrderAmount = getDiscountOfMerchant.discounttable.minimumOrderAmount
            if minimumOrderAmount <= totalAmount:
                minusValue = request.session.get('discountValue')
                # dType = getDiscountOfMerchant.discounttable.discountType
                # dValue = getDiscountOfMerchant.discounttable.maxiamt
                # discountValue = getDiscountOfMerchant.discounttable.discountValue
                
                
                # if dType == 1:
                #     minusValue = totalAmount * ((random.uniform(discountValue,dValue)) / 100)
                #     #totalAmount -= minusValue
                # else:
                #     minusValue = random.uniform(discountValue,dValue)
                
                totalAmount -= minusValue
                getofferprice += minusValue

    
        output = {"totalPrice": round(totalAmount, 2),
                  "valueReduced": getofferprice,
                  "taxes": showtaxes,
                  "productTotalIncludingTax": totalProductPrice,
                  "deliveryCharge": deliveryCharge,
                  "preparationTime": preparationTime,
                  "duration": duration,
                  "distance": distance,
                  "tipAmount": om.tipAmount,
                  "otpForOrder":generatedOtp
                  }
        
        addorder.totalAmount = round(totalAmount, 2)
        addorder.deliveryCharge = deliveryCharge

        if om.couponCode != "":
            addordercoupon = orderCouponsTable(orderId= addorder.orderId, couponId= coupon, valueReduced= getofferprice)
            db.add(addordercoupon)

        if om.paymentMethod == "1":
        # orderAcceptanceTime = 40
            expectedOrderAcceptance = current + timedelta(seconds=orderAcceptanceTime)
            background_tasks.add_task(schedule_merchant, expectedOrderAcceptance, addorder.orderId, db)
        db.commit()
        message = ({'message': 'new order placed','orderId': addorder.orderId, 'userId':userId})
        if getorderaccept.autoAccept == 1:
        #     message.update({
        #     'clientconnectionId':clientconnectionId, 'receiverconnectionId':receiverconnectionId
        # })
            # await send_message_fun(db,message,userId,merchantUserId,0,om.merchantId,addorder.orderId)
            # await sentPersonal(message,'1$0') #assuming that the first member is the admin
            # message = ({'message': 'unable to find an agent for this order','orderId': addorder.orderId, 'userId':userId})
            await notifyperson(db,message,1,0,addorder.orderId)

        await send_message_fun(db,message,userId,merchantUserId,0,om.merchantId,addorder.orderId)
        getterminology1 = db.query(terminologyTable.terminology).filter(terminologyTable.type == 1, terminologyTable.subType == 1).scalar()

        return JSONResponse(status_code=200, content={"detail": getterminology1 if getterminology1 else "order placed successfully", "charges":output})
    except Exception as e:
        print(e)
      
        db.rollback()
        #db.query(ordersTable).filter(ordersTable.orderId == addorder.orderId).delete()
        #db.commit()  
        return JSONResponse(status_code=400, content={"detail": "unable to place order"})



@router.post("/view-orders", tags=["Orders"])
async def viewOrders(p:orderpagination, db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):

    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')

    limit = int(p.limit) if p.limit else 10
    page = int(p.page) if p.page else 1
    offset = limit * (page - 1)
    if userType != "admin" and userType != "customer" and userType != "merchant" and userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    userId = decoded_token.get('userId')

    #,joinedload(ordersTable.orderRelation3)
    try:
        fetch = db.query(ordersTable).options(joinedload(ordersTable.orderRelation2).joinedload(merchantTable.merchantImage),joinedload(ordersTable.orderRelation5).joinedload(orderItemsTable.orderItemsRelation2).joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2),joinedload(ordersTable.orderpayment),joinedload(ordersTable.orderrefund))
        #joinedload(ordersTable.orderRelation4).joinedload(orderCouponsTable.ordersCouponRelation2)

        if userType == "customer":
            fetch = fetch.filter(ordersTable.userId == userId)
        if userType == "merchant":
            # getMerchantId = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
            fetch = fetch.filter(ordersTable.merchantId == int(p.merchantId))

        if userType == "deliveryAgent":
            fetch = fetch.filter(ordersTable.deliveryAgentId == userId)

        if p.orderStatus != "":
            if p.orderStatus == "0":
                fetch = fetch.filter(ordersTable.orderStatus == 0,ordersTable.status == 0) #pending orders
            if p.orderStatus == "1":
                fetch = fetch.filter(ordersTable.orderStatus == 1,ordersTable.status == 0) #dispatched orders
            if p.orderStatus == "2":
                fetch = fetch.filter(ordersTable.orderStatus == 2,ordersTable.status == 0) #completed orders
            if p.orderStatus == "3":
                fetch = fetch.filter(ordersTable.status == 1) #cancelled orders
            # if p.orderStatus == "4":
            #     fetch = fetch.filter(ordersTable.status == 1) #cancelled orders

        if p.search != "":
            fetch = fetch.filter(ordersTable.orderId == int(p.search))
       
        totalCount = fetch.count()
        #   fetch = fetch.join(ordersTable.orderRelation5).filter(orderItemsTable.status == 0)
        fetch = fetch.order_by(ordersTable.orderId.desc()).limit(limit).offset(offset).all()
        if fetch is not None:
            return JSONResponse(status_code=200, content={"detail":jsonable_encoder(fetch), "totalCount":totalCount})
        else:
            return JSONResponse(status_code=200, content={"detail":[], "totalCount":totalCount})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": []})


@router.get("/order-single/{orderId}", tags=["Orders"])
async def orderSingle(orderId:int,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')

    if userType != "admin" and userType != "customer" and userType != "merchant" and userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    userId = decoded_token.get('userId')

    try:
        getPreference = db.query(PreferenceTable).first()

        fetch = db.query(ordersTable).options(joinedload(ordersTable.orderRelation2).joinedload(merchantTable.merchantImage),joinedload(ordersTable.orderRelation4).joinedload(orderCouponsTable.ordersCouponRelation2),joinedload(ordersTable.orderRelation5).joinedload(orderItemsTable.orderItemsRelation2).joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2),joinedload(ordersTable.ordereduser).joinedload(users.userrelation2), joinedload(ordersTable.orderdeliveryrelation).joinedload(orderDeliveryModel.deliveryagentuser).joinedload(users.userdeliveryagentpersonal))

        rateMerchant = 0
        if userType == "customer":
            checkReviewStatus = db.query(orderSettingsModel).first()
            if checkReviewStatus is not None and checkReviewStatus.allowCustomersToRate == 1:
                rateMerchant = 1
            fetch = fetch.filter(ordersTable.userId == userId)
        if userType == "merchant":
            getMerchantId = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
            fetch = fetch.filter(ordersTable.merchantId == getMerchantId)

        if userType == "deliveryAgent":
            fetch = fetch.filter(ordersTable.deliveryAgentId == userId)

        fetch = fetch.filter(ordersTable.orderId == orderId).first()
        if fetch is not None:
            return JSONResponse(status_code=200, content={"detail":jsonable_encoder(fetch),"rateMerchant":rateMerchant}) #,"acceptOrRejectMerchant":getPreference.showacceptOrrejectmerchants
        else:
            return JSONResponse(status_code=200, content={"detail":[]})
       
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": []})

#add new product change address

@router.put("/edit-order/{orderId}", tags=["Orders"])
async def editOrder(orderId:int,ob:editOrderModel, db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')

    if userType != "admin" and userType != "manager" and userType != "merchant":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    try:
        whoCanEdit = db.query(orderSettingsModel).first()
        if whoCanEdit is None and userType != "admin":
            
            return JSONResponse(status_code=406, content={"detail": "you do not have permission to edit"})
            
        if whoCanEdit.allowMerchantToEdit == 0 and userType == "merchant":
            return JSONResponse(status_code=406, content={"detail": "permission for merchant to edit order is not enabled"})

        if whoCanEdit.allowManagerToEdit == 0 and userType == "manager":
            return JSONResponse(status_code=406, content={"detail": "permission for manager to edit order is not enabled"})

        getdelivery = db.query(deliverysettingTable.chargePerKm).scalar()
        deliveryChargePerKm = getdelivery if getdelivery else 10 
        fetch = db.query(ordersTable).filter(ordersTable.orderId == orderId)
        if userType == "merchant":
            getmerchant = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
            fetch = fetch.filter(ordersTable.merchantId == getmerchant)

        fetch = fetch.first()
        
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail": "order not found"})
        
        if fetch.orderStatus != 0 and fetch.orderStatus != 3:
            return JSONResponse(status_code=406, content={"detail": "order picked up from merchant you cannot edit order anymore"})
        
        merchantId = fetch.merchantId
        
        valueReduced = fetch.valueReduced
       
        oldTotal = fetch.totalAmount
        durationDelivery = fetch.durationFromMerchant


        newPrice = 0
        dataFromOrderDelivery = db.query(orderDeliveryModel).filter(orderDeliveryModel.orderId == orderId).first()

        #expectedArrival = dataFromOrderDelivery.expectedArrival

        if ob.latitude != "" and ob.longitude != "" and ob.address != "":
             #await reverseGeocode(ob.latitude,ob.longitude)
            fetch.latitude = ob.latitude
            fetch.longitude = ob.longitude
            fetch.orderedAddress = ob.address
            merchantCoordinates = db.query(merchantTable).filter(merchantTable.merchantId == merchantId).first()
            if merchantCoordinates is None:
                return JSONResponse(status_code=403, content={"detail": "merchant not found"})
            

            getalldata = await distanceCalculate(ob.latitude, ob.longitude, merchantCoordinates.latitude, merchantCoordinates.longitude)   

            mapstatus = getalldata['status']
            distance = getalldata['rows'][0]['elements'][0]['distance']
            duration = getalldata['rows'][0]['elements'][0]['duration']

            if mapstatus != "SUCCESS":
                return JSONResponse(status_code=404, content={"detail": "unable to calculate distance to your current location"})
            

            distanceInKm = round(distance / 1000, 2)
            durationInMin = round(duration / 60, 2) #new duration for the journey
            deliveryCharge = round(distanceInKm * deliveryChargePerKm, 2)
            fetch.durationFromMerchant = durationInMin
            newPrice += deliveryCharge

            if durationDelivery > durationInMin:
                differenceInDuration = durationDelivery - durationInMin
                dataFromOrderDelivery.expectedArrival -= timedelta(minutes= differenceInDuration)
            else:
                differenceInDuration = durationInMin - durationDelivery
                dataFromOrderDelivery.expectedArrival += timedelta(minutes= differenceInDuration)



        # getorderitems = db.query(orderItemsTable).filter(orderItemsTable.orderId == orderId).all()
        # if getorderitems is None:
        #     return JSONResponse(status_code=404, content={"detail": "order items not found"})
        
        #return getorderitems
 
       
        if len(ob.order) > 0:
            
            # productCost = db.query(func.sum(orderItemsTable.productTotal)).filter(orderItemsTable.orderId == orderId).all()
            # print(productCost)
            db.query(orderItemsTable).filter(orderItemsTable.orderId == orderId).delete()
            for i in ob.order:
                getPrice = db.query(productsTable).filter(productsTable.productId == i.productId).first()
                totalProductPrice = getPrice.price * int(i.quantity)
                getproductTax = db.query(productTaxTable).options(joinedload(productTaxTable.producttaxrelation)).filter(productTaxTable.productId == i.productId).all()

                if getproductTax is not None:
                    for item in getproductTax:
                       
                        totalProductPrice += (int(i.quantity) * round(item.taxAmount, 2))
                newPrice += totalProductPrice
                
                orderProducts = orderItemsTable(productId=int(i.productId), quantity= int(i.quantity), price= getPrice.price, productTotal= totalProductPrice, orderId= orderId)
                db.add(orderProducts)

        newPrice -= valueReduced
        newPrice += fetch.tipAmount

        # if new price is greater than old price then it has to be collected from customer when the delivery is made

        if newPrice > oldTotal:
            if fetch.paymentMethod == "0": #it is online payment
                amountToBeCollected = newPrice - oldTotal
                dataFromOrderDelivery.amountToBeCollected += amountToBeCollected
            else: #it is cash on delivery
                dataFromOrderDelivery.amountToBeCollected = newPrice
        # if new price is less then old price the remaining amount has to be added to customer loyality points       
        else:
            if fetch.paymentMethod == "1":

                dataFromOrderDelivery.amountToBeCollected = newPrice
            amountToBeCollected = oldTotal - newPrice
            fetchpointCriterion = db.query(Loyality).first()
            if fetchpointCriterion is None:
                return JSONResponse(status_code=404, content={"detail": "point criterion not found"})
            
            calculatePointsForUser = (fetchpointCriterion.earningCriteriaAmount / amountToBeCollected) * fetchpointCriterion.earningCriteriaPoint

            fetchFromLoyality = db.query(loyalityPointsTable).filter(loyalityPointsTable.userId == fetch.userId).first()
            if fetchFromLoyality is None:
                addtolo = loyalityPointsTable(userId= fetch.userId, points= calculatePointsForUser)
                db.add(addtolo)
            else:
                fetchFromLoyality.points += calculatePointsForUser
        #update total amount in order table
        fetch.totalAmount = newPrice
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "order edited successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to edit order"})

@router.put("/user-cancelorder/{orderId}", tags=["Orders"])
async def userCancelOrder(orderId:int,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')

    if userType != "customer":
        return JSONResponse(status_code=403, content={"detail": "you lack customer privilages"})
    try:
        fetch = db.query(ordersTable).filter(ordersTable.orderId == orderId, ordersTable.userId == userId).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail": "order not found"})
        fetch.status = 1
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "order cancelled, refund will be processed shortly"})

    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to cancel order"})


@router.put("/merchant-acceptorder/{orderId}", tags=["Orders"])
async def merchantAcceptOrder(orderId:int,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')

    if userType != "merchant":
        return JSONResponse(status_code=403, content={"detail": "you lack merchant privilages"})
    try:
        
        getmerchant = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
        getOrderData = db.query(ordersTable).filter(ordersTable.orderId == orderId, ordersTable.orderStatus == 3).first()
        if getOrderData is None:
            return JSONResponse(status_code=404, content={"detail": "order not found"})
        message = ({'message': 'merchant accepted order','orderId': orderId, 'userId':getOrderData.userId})
        # totalAmount = getOrderData.totalAmount
        # getres = refund(totalAmount, orderId)
        if getOrderData.merchantId != getmerchant:
            return JSONResponse(status_code=406, content={"detail": "order does not belong to you"})
        getOrderData.orderStatus = 0
        getorderaccept = db.query(orderSettingsModel).first()
        if getorderaccept.autoAssignAgent == 1:

            longitude = float(getmerchant.longitude)
            latitude = float(getmerchant.latitude)
            radius = 90  # Define a radius in kilometers

    # Calculate bounding box for latitude and longitude
            lat_range = (latitude - (radius / 111), latitude + (radius / 111))  # Roughly 1 degree latitude = 111 km
            lon_range = (longitude - (radius / (111 * math.cos(math.radians(latitude)))), 
                        longitude + (radius / (111 * math.cos(math.radians(latitude)))))
            
            currentDay = datetime.now().date()
        
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

            getorderdelivery = db.query(orderDeliveryModel).filter(orderDeliveryModel.orderId == orderId).first()
            getorderdelivery.deliveryAgentId = deliveryAgent
        else:
            #notify admin to assign an agent
            notifyperson(db,message,1,0,orderId)
        db.commit()

        
        
        # await send_message_fun(db,message,userId,1,0,0,orderId)
        #notify ordered user
        notifyperson(db,message,getOrderData.userId,0,orderId)

        return JSONResponse(status_code=200, content={"detail": "order Accepted"})


    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to edit order"})
    

@router.put("/merchant-rejectorder/{orderId}", tags=["Orders"])
async def merchantRejectOrder(orderId:int,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')

    if userType != "merchant":
        return JSONResponse(status_code=403, content={"detail": "you lack merchant privilages"})
    try:
        getmerchant = db.query(merchantTable.merchantId).filter(merchantTable.handledByUser == userId).scalar()
        getOrderData = db.query(ordersTable).filter(ordersTable.orderId == orderId, ordersTable.orderStatus == 3, ordersTable.status == 0).first()
        if getOrderData is None:
            return JSONResponse(status_code=404, content={"detail": "order not found"})
       
        if getOrderData.merchantId != getmerchant:
            return JSONResponse(status_code=406, content={"detail": "order does not belong to you"})
        
        
        if getOrderData.paymentMethod == "0":
            totalAmount = getOrderData.totalAmount
            #print(totalAmount)
            getPaymentId = db.query(payments).filter(payments.oradoOrderId == orderId, payments.status == "captured").first()
            if getPaymentId is None:
                return JSONResponse(status_code=406, content={"detail": "payment id not found"})
            # await sentPersonal(f"orderId {orderId} got cancelled please process refund asap",1)
            message = ({'message': 'order cancelled please process refund','orderId': orderId, 'userId':getOrderData.userId})
            await notifyperson(db,message,1,0,orderId)
       
        message = ({'message': 'merchant cancelled your order','orderId': orderId, 'userId':userId})
        
        await send_message_fun(db,message,userId,1,0,0,orderId)
        # await notify(message,f'{getOrderData.userId}$0',)
           
            # getres = refund(getPaymentId.razorpayPaymentId,getPaymentId.amount)
            # if getres.get('status') != "processed":
            #     return JSONResponse(status_code=406, content={"detail": "order refund error"})
            
            # addToRefund = refundModel(userId=userId,cancelledByUserType=2,refundId= getres.get('id'),amount=getres.get('amount'),currency=getres.get('currency'),receiptId=getres.get('receipt'),razorpayPaymentId=getres.get('payment_id'),oradoOrderId= orderId)
            # db.add(addToRefund)

        getOrderData.status = 1 #cancel order
        db.commit()
        

        return JSONResponse(status_code=200, content={"detail": "order rejected"})


    except Exception as e:
        print(e)
       
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to edit order"})
    

@router.put("/agent-rejectorder/{orderId}", tags=["Orders"])
async def agentRejectOrder(orderId:int,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')

    if userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack delivery agent privilages"})
    try:
        currentDate = datetime.now().date()
        numberOfOrdersAgentRejected = db.query(func.count(agentOrderCancellationTable.orderCancellationId).filter(agentOrderCancellationTable.agentId == userId, func.date(agentOrderCancellationTable.addedAt) == currentDate)).scalar()
        #return numberOfOrdersAgentRejected
        allowedOrderRejectionPerDay = 2
        if numberOfOrdersAgentRejected >= allowedOrderRejectionPerDay:
            return JSONResponse(status_code=406, content={"detail": "you already rejected too many orders"})
        addToRejections = agentOrderCancellationTable(orderId= orderId, agentId = userId)
        db.add(addToRejections)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "order rejected successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to reject order"})
    


async def schedule_merchant(expectedOrderAcceptance,orderId,db:db_dependency):
    
    sgt_timestamp = expectedOrderAcceptance.astimezone(pytz.timezone('Asia/Singapore')) #when a job is added to db it has to trigger the scheduler
    addToMerchantSchedule = setSchedule(orderId=orderId,timeStamp=sgt_timestamp)
    db.add(addToMerchantSchedule)
    db.commit()
    db.flush()
    jobId = addToMerchantSchedule.jobId
   
    trigger = DateTrigger(run_date=sgt_timestamp)
    scheduler.add_job(
        merchantCancellation,
        trigger,
        args=[jobId, db],
        id=str(jobId),
        replace_existing=True
    )