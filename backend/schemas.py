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
    
# Schema for `testing` table
class TestingSchema(BaseModel):
    id: Optional[int]
    img_url: Optional[str]
    name: str
    role: str
    email: EmailStr

    class Config:
        from_attributes = True


# Schema for `testingtwo` table
class TestingTwoSchema(BaseModel):
    id: Optional[int]
    img_url: Optional[str]
    name: str
    date: str  # Format like "Nov 5"
    time: str  # Format like "09.00am"
    location: str
    request: str
    role: str

    class Config:
        from_attributes = True


# Schema for `insights` table
class InsightsSchema(BaseModel):
    id: Optional[int]
    heading: str
    subheading: str

    class Config:
        from_attributes = True


# Schema for `communities` table
class CommunitiesSchema(BaseModel):
    id: Optional[int]
    name: str
    logo: Optional[str]
    privacy: str
    members: str
    date: str
    notification: Optional[int]

    class Config:
        from_attributes = True