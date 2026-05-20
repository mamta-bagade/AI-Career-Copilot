from dotenv import load_dotenv
import os
import pymysql
pymysql.install_as_MySQLdb()
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
 
DATABASE_URL = os.getenv("DATABASE_URL")

engine= create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "ssl":{
            "ssl":True
        }
        
    }
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()