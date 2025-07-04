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
    
class Students(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    usn = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True,index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
class Faculties(Base):
    __tablename__ = "faculties"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True,index=True, nullable=False)
    hashed_password = Column(String, nullable=False)