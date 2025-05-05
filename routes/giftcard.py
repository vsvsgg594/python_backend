from fastapi import APIRouter,Depends
from database import db_dependency
from routes.authentication import bearer_scheme, decode_token
from typing import Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload
from fastapi.encoders import jsonable_encoder
from base_model import  giftcard,addPagination, verifyPayment
from models import Giftcard,productGallery, buyGiftCard,GiftCardModel
import uuid
from routes.payment import client
from datetime import datetime

router=APIRouter()

@router.post("/create-giftcard",tags=["GiftCard"])
async def creategiftcard(gc:giftcard,db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403,content={"detail":"You lack admin privileges"})
        # db_image = db.query(productGallery).filter(productGallery.imageId == gc.imageId).first()
        # if db_image is None:
        #     return JSONResponse(status_code=404,content={"detail":"Image not found in gallery"})
        new_card = Giftcard(name=gc.name,description=gc.description,amount=gc.amount,imageId=gc.imageId, expiry=gc.expiry)
        db.add(new_card)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "Giftcard added successfully"})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=400,content={"detail":"Unable to add Giftcard"})
    

@router.post("/view-giftcards", tags=["GiftCard"])
async def read_gift_cards(lm:addPagination,db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        limit = int(lm.limit) if lm.limit else 10
        page = int(lm.page) if lm.page else 1
        offset = limit * (page - 1)
        if user_type != "admin" and user_type != "customer" and user_type != "merchant":
            return JSONResponse(status_code=403,content={"detail":"You lack admin privileges"})
        gift_cards = db.query(Giftcard).options(joinedload(Giftcard.giftcardproductgallery)).filter(Giftcard.status == 0).limit(limit).offset(offset).all()
        if gift_cards is None:
            return JSONResponse(status_code=200, content={"detail": []})
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(gift_cards)})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=400, content={"detail": "Unable to retrieve gift cards"})
    

@router.delete("/delete-giftcards/{card_id}",tags=["GiftCard"])
async def delete_gift_card(card_id: int, db:db_dependency, token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token

        user_type = decoded_token.get('userType')
        if user_type !="admin":
            return JSONResponse(status_code=403, content={"detail":"You lack  privileges"})

        # Check if the gift card exists
        gift_card = db.query(Giftcard).filter(Giftcard.cardid == card_id).first()
        if gift_card is None:
            return JSONResponse(status_code=404, content={"detail": "Gift card not found"})
        gift_card.status = 1  # Change the status to 1
        db.commit()

        return JSONResponse(status_code=200, content={"status": 1, "detail": "Gift card deleted successfully"})

    except Exception as e:
        print(e)
        return JSONResponse(status_code=400, content={"detail": "Unable to update gift card status"})
    

@router.put("/buy-giftcard/{cardId}", tags=["GiftCard"])
async def buy_gift_cards(cardId:int,db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        userId = decoded_token.get('userId')
    
        if user_type != "admin" and user_type != "customer" and user_type != "merchant":
            return JSONResponse(status_code=403,content={"detail":"You lack admin privileges"})
        addToDb = buyGiftCard(userId=userId,giftCardId=cardId)
        db.add(addToDb)
        getgift = db.query(Giftcard).filter(Giftcard.cardid == cardId).first()
        unique_id = uuid.uuid4().hex[:8]
        reciept = "oradoGift" + "/" + unique_id
        amount = getgift.amount + "00"
      
        data = { "amount": amount, "currency": "INR", "receipt": reciept}
        payment = client.order.create(data=data)
        if payment is None:
            return  JSONResponse(status_code=400, content={"detail":[],"message":"unable to create a payment request"})

        orderId =payment.get('id')
        getPayment = GiftCardModel(giftCardId=cardId,userId=userId,orderId= orderId,recieptId=reciept,amount=amount)
        db.add(getPayment)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": payment})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=400, content={"detail": "Unable to buy gift card"})
    


@router.post("/store-giftpayment",tags=["GiftCard"])
async def storePayment(vm:verifyPayment,db:db_dependency,token: Optional[str] = Depends(bearer_scheme)): #
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    
    try:
        verify = client.utility.verify_payment_signature({
    'razorpay_order_id': vm.razorpay_order_id,
    'razorpay_payment_id': vm.razorpay_payment_id,
    'razorpay_signature': vm.razorpay_signature
    })
        
        if not verify:
            return JSONResponse(status_code=406,content={"detail":"not verified"})
        else:
            getdata =client.payment.fetch(vm.razorpay_payment_id)
            if not getdata:
                return JSONResponse(status_code=404, content={"detail":"not found"})
            else:
                #oId = getdata.get('order_id')
                status = getdata.get('status')
              
                if status == "captured":
                    store = db.query(GiftCardModel).filter(GiftCardModel.orderId == vm.razorpay_order_id).first()
                    if store is None:
                        return JSONResponse(status_code=404, content={"detail":"not found"})
                    store.razorpayPaymentId = vm.razorpay_payment_id
                    store.status = 1
                    store.transactionTime = datetime.now()
                    db.commit()
                    
                    return JSONResponse(status_code=200, content={"detail":"payment success"})
                else:
                    return JSONResponse(status_code=400, content={"detail":"payment failed"})
    except Exception as e:
        
        return JSONResponse(status_code=500, content={"detail":str(e)})
