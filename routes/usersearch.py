from fastapi import APIRouter,Depends
from models import usersearch
from base_model import keyword
from database import db_dependency
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from routes.token import decode_token, bearer_scheme

router=APIRouter()
@router.post("/user-search",tags=["UserSearch"])
def serach(ks:keyword,db:db_dependency,token: str = Depends(bearer_scheme)):
    try:
        decoded_token = decode_token(token.credentials)
        if isinstance(decoded_token, JSONResponse):
            return decoded_token
        user_type = decoded_token.get('userType')
        userid=decoded_token.get("userId")
        if user_type != "customer":
            return JSONResponse(status_code=403, detail="You lack customer privileges")
        db_keyword = usersearch(userId=userid,keyword=ks.keyword)

        # Add to the session and commit
        db.add(db_keyword)
        db.commit()
        db.refresh(db_keyword)  # Optionally refresh to get updated fields

        return JSONResponse(status_code=200, content={"detail": "keyword added successfully"})
    except Exception as e:
        print(e)
        return JSONResponse(status_code=400,content={"detail":"Unable to add keyword"})