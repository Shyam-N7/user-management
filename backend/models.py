from sqlalchemy import Column, Integer, String
#Base class  all models inherit from
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    
class Users(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    email = Column(String, unique=True,index=True, nullable=False)
    hashed_password = Column(String, nullable=False)