# used to establish database connection
from sqlalchemy import create_engine
#create db session and define db models
from sqlalchemy.orm import sessionmaker, declarative_base
#read environment variables
import os
#access credentials
from dotenv import load_dotenv

load_dotenv()

SQL_ALCHEMY_DB_URL = os.getenv("DATABASE_URL")

engine = create_engine(SQL_ALCHEMY_DB_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#base class for all sql_al models
Base = declarative_base()