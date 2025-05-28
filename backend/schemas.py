from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: str
    
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

    #allows sqlalchemy to convert into JSON
    class Config:
        from_attributes = True
        
class UserDelete(BaseModel):
    reason: str
    
class AddNumbers(BaseModel):
    a: int
    b: int
    
class ToFarenheit(BaseModel):
    celsius: float
    
class SalaryUpdate(BaseModel):
    new_salary: int
    
class AddEmployee(BaseModel):
    emp_name: str
    emp_salary: int
    
class SalaryIncrease(BaseModel):
    increase_percent: int
    
class ClientCreate(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr
    password: str
    
class ClientResponse(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: EmailStr
    detail: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class Token(BaseModel):
    access_token: str
    token_type: str