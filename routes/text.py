from fastapi import APIRouter,Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from base_model import timeslot,edittime
from database import db_dependency
from routes.token import decode_token,bearer_scheme
from models import Timeslot

router=APIRouter()


@router.post("/create-timeslot",tags=["TimeSlot"])
def createtime(ts:timeslot,db:db_dependency,token: str=Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"detail": "You lack admin privileges"})
        
        time=Timeslot(StartTime=ts.starttime,EndTime=ts.endtime,MaxiAmount=ts.maxiamount)
        db.add(time)
        db.commit()
        
        return JSONResponse(status_code=200, content={"detail": "Timeslot added successfully"})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=400, content={"detail": "Unable to add timeslot"})
    
@router.get("/view-timeslot",tags=["TimeSlot"])
def viewtimeslot(db:db_dependency,token:str=Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        if user_type != "admin" and user_type != "deliveryAgent":
            return JSONResponse(status_code=403, content={"detail": "You lack admin privileges"})
        data= db.query(Timeslot).all()
        if data is not None:
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(data)})
        else:
            return JSONResponse(status_code=200, content={"detail": []})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400,content={"detail":[]})
    
@router.post("/edit-timeslot/{shiftid}",tags=["TimeSlot"])
def edittimeslot(shiftid:int,ed:edittime,db:db_dependency,token:str=Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=404, content={"detail": "you lack privilages"})
    try:
        timedetails = db.query(Timeslot).filter(Timeslot.ShiftId==shiftid).first()
        if timedetails is None:
            return JSONResponse(status_code=404,content={"detail":"timeslot not found"})
        if ed.starttime !="":
            timedetails.StartTime =ed.starttime
        if ed.endtime !="":
            timedetails.EndTime = ed.endtime
        if ed.maxiamount !="":
            timedetails.MaxiAmount = ed.maxiamount
        db.commit()
        db.refresh(timedetails)
        return JSONResponse(status_code=200, content={"detail": "timeslot  updated successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail":"unable to update timeslot schedule"})
        

@router.delete("/delete-timeslot/{shiftid}",tags=["TimeSlot"])
def deletetimeslot(shiftid: int, db:db_dependency,token:str=Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=404, content={"detail": "you lack privilages"})
    try:
        slot = db.query(Timeslot).filter(Timeslot.ShiftId == shiftid).first()
        if slot is None:
            return JSONResponse(status_code=404,content={"detail":"timeslot not found"})
        
        db.delete(slot)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "timeslot deleted"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail":"unable to update timeslot schedule"})
        