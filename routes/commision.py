from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from database import db_dependency
from routes.token import bearer_scheme,decode_token
from models import commissionTable
from base_model import commission
router=APIRouter()


@router.get("/viewall-commission",tags=["Commission"])
async def viewallcommission(db:db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
       
    
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"detail":"You lack admin privileges" })
        # Query to join the User and ManagerTable
        commission = db.query(commissionTable).all()
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(commission)})
    except Exception as e:
        # Log the exception for debugging
        print(e)  # Replace with your logging mechanism
        return JSONResponse(status_code=400,content={"detail":"Unable to add commission details"})

@router.put("/edit-commission/{commissionId}", tags=["Commission"])
async def edit_commission(commissionId: int,cm:commission, db: db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
       
    
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
        # Retrieve the manager and associated user
        commission = db.query(commissionTable).filter(commissionTable.commissionId == commissionId).first()
        if  commission is None:
            return JSONResponse(status_code=404,content={"detail":"commission  not found"})
        # Update the manager details
        
        
        if cm.defaultCommission !="":
          commission.defaultCommission = cm.defaultCommission
        
        if cm.commissionValue !="":
          commission.commissionValue = cm.commissionValue
        
        if cm.commissiontransfer !="":
          commission.commissiontransfer = cm.commissiontransfer
        
        
   
          
        db.commit()

        return JSONResponse(status_code=200,content={"detail": "commission updated successfully"})

    except Exception as e:
        # Log the exception for debugging
        print(e)  # Replace with your logging mechanism
        return JSONResponse(status_code=400,content={"detail":"Unable to update commission"})
