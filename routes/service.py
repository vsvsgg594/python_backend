from fastapi import APIRouter,Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from database import db_dependency
from base_model import services
from routes.token import bearer_scheme,decode_token
from models import Services
router=APIRouter()
@router.post("/create-services", tags=["Services"])
def create_detail(sc:services, db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, detail="You lack admin privileges")
        db_details = Services(**sc.model_dump())
        db.add(db_details)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "details added successfully"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": "Unabel to add details "})
    
@router.get("/viewall-services",tags=["Services"])
def read_details(db:db_dependency):
    try:
        data= db.query(Services).first()
        if data is not None:
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(data)})
        else:
            return JSONResponse(status_code=200, content={"detail": []})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=500,content={"detail":[]})

# Read a single Coupon

@router.put("/edit-services/{serviceid}",tags=["Services"])
def update_details(sc:services, db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, detail="You lack admin privileges")
        db_details = db.query(Services).first()
        if db_details is None:
            return JSONResponse(status_code=404,content={"detail":"details not found"})
        if sc.termsandservices:
            db_details.termsandservices = sc.termsandservices
        
        if sc.aboutus !="":
            db_details.aboutus = sc.aboutus
        
        db.commit()
       
        return JSONResponse(status_code=200, content={"detail": "details updated successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to update details schedule"})