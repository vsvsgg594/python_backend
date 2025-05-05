from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from database import db_dependency
from models import ManagerTable,users
from sqlalchemy.orm import joinedload
from base_model import managermodel,addPagination
from routes.token import decode_token, bearer_scheme,hash_password

router=APIRouter()

@router.post("/create-manager",tags=["Manager"])
async def createmanger(mc:managermodel,db:db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        user_id=decoded_token.get('userId')
    
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
        existing_user = db.query(users).filter(
            (users.userName == mc.username) |
            (users.userEmail == mc.userEmail)
        ).first()
        if existing_user:
            return JSONResponse(status_code=400,content={"detail":"Username or email already exists"})

        new_user = users(
            userName=mc.username,
            userEmail=mc.userEmail,
            userPhone=mc.userPhone,
            userType=4,
            password=hash_password(mc.password)  
        )
        db.add(new_user)
        db.flush()
        

        new_manager = ManagerTable(
            userId=new_user.userId,  
            name=mc.name
        )

        
        db.add(new_manager)
        db.commit()

        return JSONResponse(status_code=201, content={"detail": "Manager created successfully"})

    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": "Unable to add manager"})
    
@router.get("/viewall-managers",tags=["Manager"])
async def viewallmanager(db:db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
       
    
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
        # Query to join the User and ManagerTable
        #managers = db.query(ManagerTable).options(joinedload(ManagerTable.managertableusers)).filter(users.status==1).all()
        managers = db.query(users).options(joinedload(users.usersmanagertable)).filter(users.userType == 4, users.status == 0).all()

        if managers  is None:
            return JSONResponse(status_code=200, content={"detail": []})
        # Directly return the results of the join
        return JSONResponse(status_code=200, content={"detail": jsonable_encoder(managers)})
    except Exception as e:
        # Log the exception for debugging
        print(e)  # Replace with your logging mechanism
        return JSONResponse(status_code=400,content={"detail":[],"message":"error"})
    
@router.put("/edit-manager/{userId}", tags=["Manager"])
async def edit_manager(userId: int,mc:managermodel, db: db_dependency,token: Optional[str] = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
       
    
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
        # Retrieve the manager and associated user
        user = db.query(users).filter(users.userId == userId).first()
        manager = db.query(ManagerTable).filter(ManagerTable.userId == userId).first()
        
        if  user is None:
            return JSONResponse(status_code=404,content={"detail":"user  not found"})
        if  manager is None:
            return JSONResponse(status_code=404,content={"detail":"manager  not found"})
        

        # Update the manager details
        if mc.name !="":
            manager.name = mc.name
        
        # Update the user details
        if mc.username !="":
            user.userName = mc.username
        
        if mc.userEmail !="":
            user.userEmail = mc.userEmail
        
        if mc.userPhone !="":
            user.userPhone = mc.userPhone
        
        
        if mc.password !="":
            user.password = hash_password(mc.password)  # Hash the new password

        # Commit the changes
       
        db.commit()

        return JSONResponse(status_code=200,content={"detail": "Manager and user details updated successfully"})

    except Exception as e:
        # Log the exception for debugging
        print(e)  # Replace with your logging mechanism
        return JSONResponse(status_code=400,content={"detail":"Unable to update manager"})
    
@router.delete("/delete-manager/{userId}", tags=["Manager"])
async def delete_manager(userId: int, db: db_dependency, token: Optional[str] = Depends(bearer_scheme)):
    try:
       
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        
        user_type = decoded_token.get('userType')
        
        
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"detail": "You lack admin privileges"})

        
        user = db.query(users).filter(users.userId == userId).first()
        
        if user is None:
            return JSONResponse(status_code=404, content={"detail": "User not found"})

        
        user.status = 1 
        
        # Commit the changes to the database
        db.commit()

        return JSONResponse(status_code=200, content={"detail": "Manager delete successfully"})
    
    except Exception as e:
        print(e)  # Log the exception for debugging purposes
        return JSONResponse(status_code=400, content={"detail": "Unable to delete manager"})

