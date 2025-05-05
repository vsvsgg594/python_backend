from fastapi import APIRouter,status, Depends, Form
from typing import Optional
import models
import uuid
from datetime import timedelta, datetime
from fastapi.responses import JSONResponse


from base_model import *
from database import db_dependency
from routes.token import decode_token, bearer_scheme, create_access_token, hash_password, verify_password
from routes.emailOtp import sendEmail, generate_otp

router = APIRouter()



OTP_EXPIRE_MINUTES = 50

@router.post("/signup" , summary="Signup API", tags=["Authentication"])
async def signupUser(db: db_dependency, su:signupModel):
    
    getuserName = db.query(models.users.userName).filter(models.users.userName == su.userName).scalar()
    if getuserName is not None:
        return JSONResponse(status_code=406, content={"detail":"user exists with this username"})
    getuserEmail = db.query(models.users.userEmail).filter(models.users.userEmail == su.userEmail).scalar()
    if getuserEmail is not None:
        return JSONResponse(status_code=406, content={"detail":"user exists with this email"})

    referralCode = uuid.uuid4().hex[:10]
    password = hash_password(su.password)
    referredBy = db.query(models.users.userId).filter(models.users.referralCode == su.referralCode).scalar()
    try:
        db_user = models.users(userName=su.userName,userEmail=su.userEmail,userPhone=su.userPhone, password=password, referralCode=referralCode, referredBy=referredBy)
        db.add(db_user)

       
        db.flush()
        addToLoyality = models.loyalityPointsTable(userId=db_user.userId)
        db.add(addToLoyality)
        db.commit()
        access_token = create_access_token(
        data={"userName": su.userEmail, "userId": db_user.userId, "userType": "customer"}
        )
        return JSONResponse(status_code=200, content={"detail":"user added successfully","accessToken":access_token})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=500, content={"detail":"Failed to create user"})

#login
@router.post("/login-withotp" , summary="Login API", tags=["Authentication"])
async def loginUser(db: db_dependency, em:emailModel):
    # return userName
    
    
    user = db.query(models.users).filter(models.users.userEmail == em.userEmail).first()
    myKey = uuid.uuid4().hex
    
    if user is None:
        
        return JSONResponse(status_code=404, content={"detail":"user not found"})

    elif user.status == 1:
            
        return JSONResponse(status_code=406, content={"detail":'you are blocked by admin'})

        
    generatedOtp = generate_otp(myKey)
    expireotp = timedelta(minutes=OTP_EXPIRE_MINUTES)
    timestamp = datetime.now() + expireotp
    dbOtp = models.otpStore(userEmail=em.userEmail, otp=generatedOtp, timestamp=timestamp)
    db.add(dbOtp)
    db.commit()
    result = sendEmail(em.userEmail, generatedOtp,"Please use the verification code below to sign in.","OTP To Login to Orado")
    if result is True:
        
        return JSONResponse(status_code=200, content={"detail":"OTP is sent to your email"})
    else:
        
        return JSONResponse(status_code=500, content={"detail":"unable to sent mail"})
    
@router.post("/login-withpassword" , summary="Login API", tags=["Authentication"])
async def loginUser(db: db_dependency, lg:loginModel):
    # return userName
    
    
    user = db.query(models.users).filter((models.users.userEmail == lg.input) | (models.users.userName == lg.input)).first()
    
    
    if user is None:
        
        return JSONResponse(status_code=404, content={"detail":"user not found"})

    elif user.status == 1:
            
        return JSONResponse(status_code=406, content={"detail":'you are blocked by admin'})
    
    else:
        
        if not verify_password(lg.password, user.password):
            return JSONResponse(status_code=401, content={"detail":"Invalid credentials"})

        uType = user.userType
        data={"userName": user.userEmail, "userId": user.userId}
        if uType == 0:
            userType = "customer"
        if uType == 1:
            userType = "deliveryAgent"
        if uType == 2:
            userType = "merchant"
            getmerchantIds = db.query(models.merchantTable.merchantId).filter(models.merchantTable.handledByUser == user.userId).all()
            merchant_ids = [merchant[0] for merchant in getmerchantIds]
            data.update({"merchantIds": merchant_ids})
        if uType == 3:
            userType = "admin"
        if uType == 4:
            userType == "manager"
        data.update({"userType": userType})
        access_token = create_access_token(data)
        
        return JSONResponse(status_code=200, content={"detail":access_token})

    



#otp verification
@router.post("/verifyotp",summary="Verify OTP", tags=["Authentication"])
async def verifyOtp(db: db_dependency, ot:otpModel):
    
    
    user = db.query(models.otpStore).filter(models.otpStore.userEmail == ot.userEmail).order_by(models.otpStore.slno.desc())\
    .first()
    if user is None:
        return JSONResponse(status_code=404, content={"detail":"user not found"})
    if user.status == 0:
        
        return JSONResponse(status_code= 406, content={"detail":"otp already used"})
   
    expiry = datetime.strptime(user.timestamp, '%Y-%m-%d %H:%M:%S.%f')
    current = datetime.now()
    
    if current > expiry:
        
        return JSONResponse(status_code=410, content={"detail":"otp has expired"})
    if ot.OTP != user.otp:
        return JSONResponse(status_code=401, content={"detail":"incorrect otp"})
    try:
        user.status = 0
        db.commit()

        verifiedUser = db.query(models.users).filter(models.users.userEmail == ot.userEmail).first()
        if verifiedUser is None:
            
            return JSONResponse(status_code=401, content= {"detail":"incorrect credentials"})
        userId = verifiedUser.userId
        uType = verifiedUser.userType
        data={"userName": user.userEmail, "userId": user.userId}
        if uType == 0:
            userType = "customer"
        if uType == 1:
            userType = "deliveryAgent"
        if uType == 2:
            userType = "merchant"
            getmerchantIds = db.query(models.merchantTable.merchantId).filter(models.merchantTable.handledByUser == user.userId).all()
            merchant_ids = [merchant[0] for merchant in getmerchantIds]
            data.update({"merchantIds": merchant_ids})
        if uType == 3:
            userType = "admin"
        if uType == 4:
            userType="manager"    
        data.update({"userType": userType})   
        
        access_token = create_access_token(data)
        
        return JSONResponse(status_code=200, content={"detail":access_token})
        
        
    except Exception as e:
        print(e)
        db.rollback()
        return  JSONResponse(status_code=500, content={"detail":"failed"})

#block staff and user
@router.post("/blockuser", status_code=status.HTTP_200_OK, summary="Block User", tags=["Authentication"])
async def blockUser(userId: int, db:db_dependency, token: Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    uType = decoded_token.get("userType")
    
    if uType == "superAdmin":
        blockuser = db.query(models.zippiUsers).filter(models.zippiUsers.userId == userId).first() # & (models.zippiUsers.userStatus == 0))
        if blockuser is None:
            return{"status_code":404, "detail": "user not found"}
        else:
            if blockuser.userStatus == 0:
                blockuser.userStatus = 1
                db.commit() 
                return {"status_code":200, "detail":'blocked successfully'}
            
            blockuser.userStatus = 0
            db.commit() 
            return {"status_code":200, "detail":'unblocked successfully'}

    return{"status_code":401, "detail": "you dont have admin privilages"}

@router.get("/decodetoken",summary="decode", tags=["Authentication"])
async def addsubscription(token: Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    return decoded_token
    