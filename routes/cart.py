from fastapi import APIRouter, Depends
from database import db_dependency
from routes.token import decode_token, bearer_scheme
from typing import Optional
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from base_model import myOrder, editCartModel, cartBase, viewCartBase
from models import *
from sqlalchemy.orm import joinedload
from sqlalchemy import update
from routes.helpers import check_coordinate, distanceCalculate, reverseGeocode
# from routes.order import deliveryChargePerKm
import random
from routes.emailOtp import generate_otp
from routes.chat import send_message_fun


router = APIRouter()


@router.post("/add-to-cart", tags=['Cart'])
async def addToCart(cm:myOrder,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "admin" and userType != "customer" and userType != "merchant" and userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    try:
        checkAnotherMerchant = db.query(cartTable).filter(cartTable.merchantId == cm.merchantId, cartTable.userId == userId, cartTable.status == 0).first()
        if checkAnotherMerchant is None:
            stmt = update(cartTable).filter(cartTable.userId == userId).values(status = 1)  
            db.execute(stmt)  

        checkIfProductExist = db.query(cartTable).filter(cartTable.productId == cm.productId, cartTable.userId == userId, cartTable.status == 0).first()
        if checkIfProductExist is not None:
            checkIfProductExist.quantity += cm.quantity
        else:
            addcart = cartTable(productId = cm.productId, quantity = cm.quantity, userId = userId, merchantId = cm.merchantId)
            db.add(addcart)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "successfully added to cart"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to add to cart"})
    
@router.post("/edit-cart/{cartId}", tags=['Cart'])
async def editCart(cartId:int,cm:editCartModel,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "admin" and userType != "customer" and userType != "merchant" and userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    try:
        getitem = db.query(cartTable).filter(cartTable.cartId == cartId, cartTable.userId == userId).first()
        if getitem is None:
            return JSONResponse(status_code=404, content={"detail": "item not found"})
        
        getitem.quantity = cm.quantity
      
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "successfully edited cart"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to edit cart"})

@router.post("/view-cart", tags=['Cart'])
async def viewCart(vb:viewCartBase,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "admin" and userType != "customer" and userType != "merchant" and userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    
    try:
        getdelivery = db.query(deliverysettingTable.chargePerKm).scalar()
        deliveryChargePerKm = getdelivery if getdelivery else 10 
        showtaxes = []

        # Dictionary to accumulate tax amounts
        tax_dict = {}
        totalCost = 0
        merchantId = 0
        fetch = db.query(cartTable).options(joinedload(cartTable.cartproductrelation).joinedload(productsTable.productstablerelation1)).options(joinedload(cartTable.cartproductrelation).joinedload(productsTable.productstablerelation8).joinedload(productImages.imageRelation2)).filter(cartTable.userId == userId, cartTable.status == 0).order_by(cartTable.cartId.desc()).all() #.joinedload(productsTable.productstablerelation1) .joinedload(productImages.imageRelation2) .joinedload(productsTable.productstablerelation1).
        if not fetch:
            return JSONResponse(status_code=200, content={"detail": [], "totalCost":totalCost})
        for i in fetch:
            productCost = db.query(productsTable).filter(productsTable.productId == i.productId).first()
            totalCost += (productCost.price * i.quantity)
            merchantId = productCost.merchantId
            getproductTax = db.query(productTaxTable).options(joinedload(productTaxTable.producttaxrelation)).filter(productTaxTable.productId == i.productId).all()
            if getproductTax:
                for item in getproductTax:
                    tax_name = item.producttaxrelation.taxName
                    
                    # Round the tax amount
                    tax_amount = i.quantity * round(item.taxAmount, 2)
                    totalCost += tax_amount
                    # If tax name already exists in the dictionary, add to its amount; otherwise, create a new entry
                    if tax_name in tax_dict:
                        tax_dict[tax_name] += tax_amount
                    else:
                        tax_dict[tax_name] = tax_amount
        tax_info = [{"taxName": tax_name, "taxAmount": amount} for tax_name, amount in tax_dict.items()]

        # Append the aggregated tax information to the showtaxes list
        showtaxes.append({"tax": tax_info}) 
       
        previousAddress = db.query(ordersTable.longitude, ordersTable.latitude, ordersTable.orderedAddress).filter(ordersTable.userId == userId).all()
        previousAddressList = []
        seen = set()
        if previousAddress is not None:
    
            for row in previousAddress:
                entry = (row.longitude, row.latitude, row.orderedAddress)
                if entry not in seen:
                    seen.add(entry)
                    previousAddressList.append({
                        "longitude": row.longitude, 
                        "latitude": row.latitude, 
                        "orderedAddress": row.orderedAddress
                    })
        #     previousAddressList = [
        #     {"longitude": row.longitude, "latitude": row.latitude, "orderedAddress": row.orderedAddress}
        #     for row in previousAddress
        # ]

        merchantCoordinates = db.query(merchantTable).filter(merchantTable.merchantId == merchantId).first()
        if merchantCoordinates is None:
            return JSONResponse(status_code=403, content={"detail": "merchant not found"})
        
        alldata = {
        "distance": None,
        "duration": None,
        "deliveryCharge": None,
        "taxes": showtaxes,
        "error": "Unable to calculate distance to your current location."
    }
        error = ""
        try:
            getdelivery = db.query(deliverysettingTable.chargePerKm).scalar()
            deliveryChargePerKm = getdelivery if getdelivery else 10 
            getalldata = await distanceCalculate(vb.latitude, vb.longitude, merchantCoordinates.latitude, merchantCoordinates.longitude)   

            mapstatus = getalldata['status']

            if mapstatus == "SUCCESS":
            #     return JSONResponse(status_code=404, content={"detail": "unable to calculate distance to your current location"})
                distance = getalldata['rows'][0]['elements'][0]['distance']
                duration = getalldata['rows'][0]['elements'][0]['duration']

                distanceInKm = round(distance / 1000, 2)
                durationInMin = round(duration / 60, 2)
                deliveryCharge = round(distanceInKm * deliveryChargePerKm, 2)
                totalCost += deliveryCharge
                
                alldata = {
                    "distance":distanceInKm ,
                    "duration":durationInMin,
                    "deliveryCharge": deliveryCharge,
                    "taxes": showtaxes
                }
        except Exception as e:
           error = str(e)
        # if mapstatus != "SUCCESS":
        #     return JSONResponse(status_code=404, content={"detail": "unable to calculate distance to your current location"})
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(fetch), "totalCost":totalCost,"alldata":alldata, "previousAddress": jsonable_encoder(previousAddressList),"error":error})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": []})


@router.delete("/delete-fromcart/{cartId}", tags=['Cart'])
async def deleteFromCart(cartId:int,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "admin" and userType != "customer" and userType != "merchant" and userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    
    try:
        fetch = db.query(cartTable).filter(cartTable.cartId == cartId, cartTable.userId == userId, cartTable.status == 0).first()
        if fetch is None:
            return JSONResponse(status_code=404, content={"detail": "item not found"})
        
        fetch.status = 1
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "item successfully deleted"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to delete item"})
    

@router.post("/buy-from-cart", tags=['Cart'])
async def buyFromCart(cb:cartBase,db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    userId = decoded_token.get('userId')
    if userType != "admin" and userType != "customer" and userType != "merchant" and userType != "deliveryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    
    try:
        # for i in cb.cartId:
        getdelivery = db.query(deliverysettingTable.chargePerKm).scalar()
        deliveryChargePerKm = getdelivery if getdelivery else 10 

        getgeofences = db.query(geofenceTable).filter(geofenceTable.isActive == 0, geofenceTable.status == 0).all()
        if not getgeofences:
            return JSONResponse(status_code=404, content={"detail": "geofence not found"})
        
        insideGeofence = False
        for geo in getgeofences:
             #print(geo.points)
             if check_coordinate(float(cb.latitude), float(cb.longitude), list(geo.points)):
                
                insideGeofence = True
                break
             
        if not insideGeofence:
            return JSONResponse(status_code=406, content={"detail": "sorry we dont deliver to your location"})
        

        merchantAvailability = db.query(merchantTable).filter(merchantTable.merchantId == cb.merchantId).first()
        if merchantAvailability is None:
            return JSONResponse(status_code=404, content={"detail": "merchant not found"})
        if merchantAvailability.shopStatus == 1:
            return JSONResponse(status_code=404, content={"detail": "merchant not available"})
        if merchantAvailability.status == 1:
            getterminology = db.query(terminologyTable.terminology).filter(terminologyTable.type == 1, terminologyTable.subType == 2).scalar()
            return JSONResponse(status_code=200, content={"detail": getterminology if getterminology else "merchant is not active currently"}) # fetch the terminology from terminology table
        
        currentTime = datetime.now().time()
        if merchantAvailability.openingTime > currentTime:
            return JSONResponse(status_code=200, content={"detail": "shop is not opened yet"})

        if merchantAvailability.closingTime < currentTime:
            return JSONResponse(status_code=200, content={"detail": "shop is closed for the day"})
        
        getalldata = await distanceCalculate(cb.latitude, cb.longitude, merchantAvailability.latitude, merchantAvailability.longitude)
        userAddressFromCoordinates = ""
        if cb.address == "":   
            userAddressFromCoordinates = await reverseGeocode(cb.latitude,cb.longitude)
        else:
            userAddressFromCoordinates = cb.address

        mapstatus = getalldata['status']
        if mapstatus != "SUCCESS":
            return JSONResponse(status_code=404, content={"detail": "unable to calculate distance to your current location"})
        distance = getalldata['rows'][0]['elements'][0]['distance']
        duration = getalldata['rows'][0]['elements'][0]['duration']

        
        merchantUserId = merchantAvailability.handledByUser

        distanceInKm = round(distance / 1000, 2)
        durationInMin = round(duration / 60, 2)
        deliveryCharge = round(distanceInKm * deliveryChargePerKm, 2)


        getofferprice = 0
        totalPrice = 0
        coupon = 0
        if cb.couponCode != "":
            
            getcoupon = db.query(couponsTable).filter(couponsTable.code == cb.couponCode).first()
            if getcoupon is None:
                return JSONResponse(status_code=404, content={"detail": "coupon not found"})
            coupon = getcoupon.couponId
             
            if getcoupon.startingdate > datetime.now():
                return JSONResponse(status_code=204, content={"detail": "coupon offer not started"})
            if getcoupon.endingdate < datetime.now():
                return JSONResponse(status_code=204, content={"detail": "coupon offer expired"})
            if getcoupon.maxUsers == 0:
                return JSONResponse(status_code=204, content={"detail": "coupon offer not available"})
            getcoupon.maxUsers -= 1
            getofferprice = random.randint(0, getcoupon.maxValue)
            totalPrice -= getofferprice 
            
        myKey = uuid.uuid4().hex
        generatedOtp = generate_otp(myKey)
        myorderstatus = 0
        getorderaccept = db.query(orderSettingsModel).first()
        if getorderaccept is not None:
            if getorderaccept.autoAccept != "":
                if getorderaccept.autoAccept == 0:
                    myorderstatus = 3
        addorder = ordersTable(userId= userId, merchantId= cb.merchantId,deliveryInstruction= cb.deliveryInstruction, merchantInstruction = cb.merchantInstruction, tipAmount= cb.tipAmount, deliveryMode= cb.deliveryMode, paymentMethod= cb.paymentMethod, latitude= cb.latitude, longitude=cb.longitude, orderOtp= generatedOtp, orderedAddress= userAddressFromCoordinates, orderStatus = myorderstatus)
        db.add(addorder)
        db.flush()

        

        showtaxes = []
        preparationTime = 0
        for i in cb.cartId:
            getproduc = db.query(cartTable).filter(cartTable.cartId == i).first()
            if userId != getproduc.userId:
                return JSONResponse(status_code=406, content={"detail": "this cart does not belong to you"})
            
            getPrice = db.query(productsTable).filter(productsTable.productId == getproduc.productId).first()
            totalProductPrice = getPrice.price * getproduc.quantity
            productName = getPrice.productName
            preparationTime += int(getPrice.preparationTime)
            orderProducts = orderItemsTable(productId=getproduc.productId, quantity= getproduc.quantity, price= getPrice.price, productTotal= totalProductPrice, orderId= addorder.orderId)
            db.add(orderProducts)

            totalPrice += totalProductPrice
            getproductTax = db.query(productTaxTable).options(joinedload(productTaxTable.producttaxrelation)).filter(productTaxTable.productId == getproduc.productId).all()
            tax_info = []
            if getproductTax is not None:
                for item in getproductTax:
                    
                    tax_name = item.producttaxrelation.taxName
                    
                    totalPrice += round(item.taxAmount, 2)
                    
                    tax_info.append({
                        "taxAmount": round(item.taxAmount, 2),
                        "taxName": tax_name,
                        
                    })

            showtaxes.append({"productName":productName,"tax":tax_info})
        
        totalAmount = totalPrice

  
        totalAmount += deliveryCharge
        totalAmount += cb.tipAmount
    
        output = {"totalPrice": totalAmount,
                  "valueReduced": getofferprice,
                  "taxes": showtaxes,
                  "deliveryCharge": deliveryCharge,
                  "preparationTime": preparationTime,
                  "duration": durationInMin,
                  "distance": distanceInKm,
                  "tipAmount": cb.tipAmount,
                  "otpForOrder":generatedOtp
                  }
        
        addorder.totalAmount = round(totalAmount, 2)

        if cb.couponCode != "":
            addordercoupon = orderCouponsTable(orderId= addorder.orderId, couponId= coupon, valueReduced= getofferprice)
            db.add(addordercoupon)

        db.commit()
        # connectionId = str(userId) + "$" + "0"
        # await send_message_fun(db,f"new order placed orderId {addorder.orderId}",userId,merchantUserId,0,cb.merchantId)
        message = ({'message': 'new order placed','orderId': addorder.orderId, 'userId':userId})
        
        await send_message_fun(db,message,userId,merchantUserId,0,cb.merchantId,addorder.orderId)
        getterminology1 = db.query(terminologyTable.terminology).filter(terminologyTable.type == 1, terminologyTable.subType == 1).scalar()

        return JSONResponse(status_code=200, content={"detail": getterminology1 if getterminology1 else "order placed successfully", "charges":output})


    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to order"})