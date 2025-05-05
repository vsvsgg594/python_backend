from fastapi import APIRouter,Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from database import db_dependency
from base_model import terminology,addPagination, terminologyEdit
from routes.token import bearer_scheme,decode_token
from models import terminologyTable

router=APIRouter()

@router.post("/create-terminology",summary="for terminologies there is type and subtype type refers to order, product etc type 1 is order, there is only one terminology allowed for a subtype of a type. the subtypes 1,2,..11 are found in screenshot and should be looped in frontend according to that",tags=["Terminology"])
def createterminology(ty:terminology,db:db_dependency,token:str=Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
        
        checkifExists = db.query(terminologyTable).filter(terminologyTable.type == ty.type, terminologyTable.subType == ty.subType).first()
        if checkifExists is not None:
            return JSONResponse(status_code=406, content={"detail":"already a terminology is present for this type and subtype"})
                                
        db_terminology= terminologyTable(type=ty.type,subType= ty.subType,terminology=ty.terminology)

        # Add to the session and commit
        db.add(db_terminology)
        db.commit()
            # Optionally refresh to get updated fields

        return JSONResponse(status_code=200, content={"detail": "Terminology  added successfully"})
    except Exception as e:
            print(e)
            return JSONResponse(status_code=400,content={"detail":"Unable to add Terminology"})
    
    
@router.get("/viewall-terminology",tags=["Terminology"])
def viewallfeedback(db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
       
        if user_type != "admin":
            return JSONResponse(status_code=403,content={"detail":"You lack admin privileges"})
        
        data= db.query(terminologyTable).all()
        if data is not None:
            return JSONResponse(status_code=200, content={"detail": jsonable_encoder(data)})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400,content={"detail":[]})
    

@router.put("/edit-terminology/{terminologyId}",tags=["Terminology"])
def update_details(terminologyId:int,ty:terminologyEdit,db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        if user_type != "admin":
            return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
        db_details = db.query(terminologyTable).filter(terminologyTable.terminologyid==terminologyId).first()
        if db_details is None:
            return JSONResponse(status_code=404,content={"detail":"terminology not found"})
       
        if ty.terminology !="":
            db_details.terminology = ty.terminology
        
        db.commit()
       
        return JSONResponse(status_code=200, content={"detail": "terminology updated successfully"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail": "unable to update terminology "})
    

@router.delete("/delete-terminology/{terminologyId}",tags=["Terminology"])
def delete_coupon(terminologyId:int, db:db_dependency,token: str = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    userType = decoded_token.get('userType')
    if userType != "admin":
        return JSONResponse(status_code=404, content={"detail": "you lack admin privilages"})
    try:
        db_terminology= db.query(terminologyTable).filter(terminologyTable.terminologyid ==terminologyId).first()
        if db_terminology is None:
            return JSONResponse(status_code=404,content={"detail":"terminology not found"})
            
        db.delete(db_terminology)
        db.commit()
        return JSONResponse(status_code=200, content={"detail": "terminology deleted"})
    except Exception as e:
        print(e)
        db.rollback()
        return JSONResponse(status_code=400, content={"detail":"unable to de terminology schedule"})

