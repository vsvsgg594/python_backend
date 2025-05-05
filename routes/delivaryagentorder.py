from fastapi import APIRouter,Depends
from database import db_dependency
from routes.authentication import bearer_scheme, decode_token
from typing import Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload
from fastapi.encoders import jsonable_encoder
from base_model import  delivaryagentorder
from models import *


router = APIRouter()
@router.post("/view-agentorder", tags=["Delivaryagentorder"])
def deliveryagentorder(p:delivaryagentorder, db:db_dependency, token:Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    limit = int(p.limit) if p.limit else 10
    page = int(p.page) if p.page else 1
    offset = limit * (page - 1)
    if userType != "delivaryAgent":
        return JSONResponse(status_code=403, content={"detail": "you lack user privilages"})
    userId = decoded_token.get('userId')
    try:
        fetch = db.query(orderDeliveryModel).options(joinedload(orderDeliveryModel.deliveryorderrelation)).limit(limit).offset(offset).all()
        return JSONResponse(status_code=200, content={"detail":jsonable_encoder(fetch)})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": []})