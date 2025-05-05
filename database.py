from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
from typing import Annotated
from fastapi import Depends

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

load_dotenv(dotenv_path)

USERNAME = os.getenv('UNAME')
PASSWORD = os.getenv('PASSWORD')
HOST = os.getenv('HOST')
DBNAME = os.getenv('DBNAME')

# print ("uname",USERNAME)


URL_DATABASE = f'postgresql://{USERNAME}:{PASSWORD}@{HOST}/{DBNAME}' #mysql+pymysql

engine = create_engine(URL_DATABASE,pool_size=10, max_overflow=20)

# if not database_exists(engine.url):
#     create_database(engine.url)
#     print("Database created successfully!")
# else:
#     print("Database already exists.")

SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)
Base = declarative_base()

def get_db(): 
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# with engine.connect() as connection:
#         connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))