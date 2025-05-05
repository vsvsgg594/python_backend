from fastapi import APIRouter, Depends
from database import db_dependency
from routes.token import decode_token, bearer_scheme
from models import geofenceTable, PreferenceTable
from base_model import geofenceCreate, geofenceEdit
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

router = APIRouter()


@router.post("/add-geofence",tags=["Geofence"])
async def create_geofence(geofence: geofenceCreate, db: db_dependency,token:str= Depends(bearer_scheme)):
    
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    user_type = decoded_token.get('userType')
    if user_type != "admin":
        return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
    try:
        # Flatten the points into a single list for storage
        #flat_points = [coord for point in geofence.points for coord in point]  # [lat1, lon1, lat2, lon2, ...]
        
        # Create a new geofence entry
        db_geofence = geofenceTable(geofenceName=geofence.geofenceName, points=geofence.points)
        db.add(db_geofence)
        db.commit()
        return JSONResponse(status_code=200,content={"detail":"geofence added"})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500,content={"detail":"unable to add geofence"})
    

@router.get("/viewall-geofences",tags=["Geofence"])
async def viewallgeofence(db:db_dependency,token: str = Depends(bearer_scheme)):
    
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    user_type = decoded_token.get('userType')
    
    if user_type != "admin" and user_type != "merchant":
        return JSONResponse(status_code=403,content={"detail":"You lack admin privileges"})
    
    if user_type == "merchant":
        checkIfMerchantCanView = db.query(PreferenceTable).first()
        if checkIfMerchantCanView is None or checkIfMerchantCanView.showGeofenceToMerchant == 0:
            return JSONResponse(status_code=406,content={"detail":"you dont have viewing privilage"})
    
   

    try:
        
        data= db.query(geofenceTable).all()
        if data is not None:
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(data)})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400,content={"detail":[]})
    
@router.put("/edit-geofence/{geofenceId}",tags=["Geofence"])
async def updateGeofence(geofenceId:int,ty:geofenceEdit,db:db_dependency,token: str = Depends(bearer_scheme)):
    
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    user_type = decoded_token.get('userType')
    if user_type != "admin":
        return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
    
    try:
        fetch = db.query(geofenceTable).filter(geofenceTable.geofenceId==geofenceId).first()
        if fetch is None:
            return JSONResponse(status_code=404,content={"detail":"geofence not found"})
       
        if ty.geofenceName !="":
            fetch.geofenceName = ty.geofenceName
        if ty.isActive !="":
            fetch.isActive = ty.isActive
        if ty.points !="":
            #fetch.points = [coord for point in ty.points for coord in point] 
            fetch.points = ty.points
        
        db.commit()
       
        return JSONResponse(status_code=200, content={"detail": "geofence updated successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to update geofence "})
    

@router.delete("/delete-geofence/{geofenceId}",tags=["Geofence"])
async def deleteGeofence(geofenceId:int, db:db_dependency,token: str = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=404, content={"detail": "you lack admin privilages"})
    try:
        fetch= db.query(geofenceTable).filter(geofenceTable.geofenceId == geofenceId, geofenceTable.status == 0).first()
        if fetch is None:
            return JSONResponse(status_code=404,content={"detail":"geofence not found"})
            
        fetch.status = 1
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "geofence deleted"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail":"unable to de geofence schedule"})
    
