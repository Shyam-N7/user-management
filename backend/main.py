from fastapi import FastAPI, Depends, HTTPException, Request
#Depends allows to pass dependencies
from sqlalchemy.orm import Session
import models, schemas, crud
from database import engine_main, engine_users
from dependencies import get_db_main, get_db_users
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body
from fastapi.security import HTTPBearer
from auth import create_access_token
from typing import List
import logging
import re
from collections import defaultdict
from typing import Optional
import time
import hashlib
from datetime import datetime, timedelta
from auth import (create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

security = HTTPBearer()

login_attempts = defaultdict(list)
blocked_ips = defaultdict(float)

MAX_LOGIN_ATTEMPTS = 5
BLOCK_DURATION = 900
ATTEMPT_WINDOW = 300

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://user-management-lovat.vercel.app", "https://student-portal-pearl.vercel.app"],  # Allow all origins
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

#Create db tables if they don't exist
models.Base.metadata.create_all(bind=engine_main)
models.Base.metadata.create_all(bind=engine_users)

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI!"}

@app.post("/users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db_main)):
    user = crud.create_user(db=db, user=user)
    return user

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db_main)):
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get('/users', response_model=List[schemas.UserResponse])
def get_all_users(db: Session = Depends(get_db_main)):
    users = crud.get_all_users(db)
    return users

@app.put('/users/{user_id}', response_model=schemas.UserResponse)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db_main)):
    updated_user = crud.update_user(db, user_id, user)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@app.delete('/users/{user_id}', response_model=dict)
def delete_user(user_id: int, db: Session = Depends(get_db_main)):
    deleted_user = crud.delete_user(db, user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully", "user": deleted_user}

# USERS REGISTER AND LOGIN
# @app.post('/register', response_model = schemas.ClientResponse)
# def register(user: schemas.ClientCreate, db: Session = Depends(get_db_users)):
#     return crud.create_client(db, user)

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_name_field(name: str, field_name: str) -> bool:
    if not name or len(name.strip()) == 0:
        return False
    
    if len(name) > 50:  # Reasonable length limit
        return False
    
    # Allow only letters, spaces, hyphens, apostrophes
    pattern = r'^[a-zA-Z\s\-]+$'
    if not re.match(pattern, name):
        return False
    
    return True

def validate_password_strength(password: str) -> bool:
    if len(password) < 8:
        return False
    if len(password) > 128:  # Prevent DoS
        return False
    if not re.search(r'[A-Z]', password):  # Uppercase
        return False
    if not re.search(r'[a-z]', password):  # Lowercase
        return False
    if not re.search(r'\d', password):     # Number
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):  # Special char
        return False
    
    return True

def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host

def is_rate_limited(ip_address: str) -> tuple[bool, Optional[str]]:
    current_time = time.time()
    
    # Check if IP is currently blocked
    if ip_address in blocked_ips:
        if current_time < blocked_ips[ip_address]:
            remaining_time = int(blocked_ips[ip_address] - current_time)
            return True, f"Too many failed attempts. Try again in {remaining_time} seconds"
        else:
            del blocked_ips[ip_address]
            login_attempts[ip_address] = []
    
    # Clean old attempts
    cutoff_time = current_time - ATTEMPT_WINDOW
    login_attempts[ip_address] = [
        attempt_time for attempt_time in login_attempts[ip_address] 
        if attempt_time > cutoff_time
    ]
    
    # Check if too many attempts
    if len(login_attempts[ip_address]) >= MAX_LOGIN_ATTEMPTS:
        blocked_ips[ip_address] = current_time + BLOCK_DURATION
        logger.warning(f"IP {ip_address} blocked due to too many failed login attempts")
        return True, f"Too many failed attempts. Blocked for {BLOCK_DURATION // 60} minutes"
    
    return False, None

def record_failed_attempt(ip_address: str):
    # Records failed login for rate limiting
    current_time = time.time()
    login_attempts[ip_address].append(current_time)
    
def sanitize_input(input_string: str) -> str:
    if not input_string:
        return ""
    
    # Remove dangerous characters
    sanitized = input_string.replace('\x00', '').strip()
    return sanitized[:255]

def hash_sensitive_data(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()[:8]


@app.post('/register', response_model=schemas.ClientResponse)
def register(user: schemas.ClientCreate, request: Request, db: Session = Depends(get_db_users)):
    
    client_ip = get_client_ip(request)
    
    is_limited, limit_message = is_rate_limited(client_ip)
    if is_limited:
        logger.warning(f"Registration rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail=limit_message)
    
    try:
        if not user.email or not user.password or not user.firstname or not user.lastname:
            logger.warning(f"Registration attempt with missing fields from IP: {client_ip}")
            raise HTTPException(
                status_code=400,
                detail="All fields (firstname, lastname, email, password) are required"
            )
        
        sanitized_firstname = sanitize_input(user.firstname)
        sanitized_lastname = sanitize_input(user.lastname)
        sanitized_email = sanitize_input(user.email.lower())
        sanitized_password = sanitize_input(user.password)
        
        if not validate_email(sanitized_email):
            logger.warning(f"Invalid email format in registration from IP: {client_ip}")
            record_failed_attempt(client_ip)  # Count as failed attempt
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        if not validate_name_field(sanitized_firstname, "First name"):
            record_failed_attempt(client_ip)
            raise HTTPException(status_code=400, detail="Invalid first name")
            
        if not validate_name_field(sanitized_lastname, "Last name"):
            record_failed_attempt(client_ip)
            raise HTTPException(status_code=400, detail="Invalid last name")
        
        if not validate_password_strength(sanitized_password):
            record_failed_attempt(client_ip)
            raise HTTPException(
                status_code=400, 
                detail="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
            )
        
        logger.info(f"Registration attempt for email hash: {hash_sensitive_data(sanitized_email)} from IP: {client_ip}")
        
        sanitized_user = schemas.ClientCreate(
            firstname=sanitized_firstname,
            lastname=sanitized_lastname,
            email=sanitized_email,
            password=sanitized_password
        )
        
        new_client = crud.create_client(db, sanitized_user)
        
        logger.info(f"Successful registration for user ID: {new_client.id} from IP: {client_ip}")
        
        if client_ip in login_attempts:
            login_attempts[client_ip] = []
        
        return new_client
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected registration error for IP: {client_ip}, Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred during registration"
        )


@app.post('/login')
def login(user: schemas.UserLogin, request: Request, db: Session = Depends(get_db_users)):
    
    client_ip = get_client_ip(request)
    
    # Step 2: Check rate limiting
    is_limited, limit_message = is_rate_limited(client_ip)
    if is_limited:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail=limit_message)
    
    try:
        
        # Input valiation
        if not user.email or not user.password:
            logger.warning(f"Login attempt with missing credentials from IP: {client_ip}")
            raise HTTPException(
                status_code=400,
                detail="Email and password are required"
            )
        
        sanitized_email = sanitize_input(user.email.lower())
        sanitized_password = sanitize_input(user.password)
        
        if not validate_email(sanitized_email):
            logger.warning(f"Invalid email format attempted from IP: {client_ip}")
            record_failed_attempt(client_ip)
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        logger.info(f"Login attempt for email hash: {hash_sensitive_data(sanitized_email)} from IP: {client_ip}")
        
        sanitized_user = schemas.UserLogin(
            email=sanitized_email,
            password=sanitized_password
        )
        
        authenticated =  crud.authenticate_client(db, sanitized_user)
        if not authenticated:
            record_failed_attempt(client_ip)
            logger.warning(
                f"Failed login attempt for email hash: {hash_sensitive_data(sanitized_email)} "
                f"from IP: {client_ip}"
            )
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        access_token = create_access_token(data = {"sub": authenticated.id})
        logger.info(f"Successful login for user ID: {authenticated.id} from IP: {client_ip}")
        
        if client_ip in login_attempts:
            login_attempts[client_ip] = []
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": authenticated.id,
                "firstname": authenticated.firstname,
                "lastname": authenticated.lastname,
                "email": authenticated.email
            },
            "message": authenticated.detail,
            "login_timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected login error for IP: {client_ip}, Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred during login"
        )

@app.get('/square/{number}')
def get_square(number: int, db: Session = Depends(get_db_main)):
    return crud.get_square(db, number)

@app.post('/add_numbers')
def add_numbers(num: schemas.AddNumbers, db:Session = Depends(get_db_main)):
    return crud.add_number(db, num.a, num.b)

@app.post('/celsius_to_fahrenheit')
def celsius_to_fahrenheit(temperature: schemas.ToFarenheit, db: Session = Depends(get_db_main)):
    return crud.celsius_to_farenheit(db, temperature.celsius)

@app.get('/check_even_odd/{number}')
def check_even_odd(number: int, db: Session = Depends(get_db_main)):
    return crud.check_even_odd(db, number)

@app.get('/high_salary_employees/{salary_threshold}')
def high_salary_employees(salary_threshold: int, db: Session = Depends(get_db_main)):
    return crud.get_high_salary_employees(db, salary_threshold)

@app.get('/get_employee_salary/{emp_id}')
def get_employee_salary(emp_id: int, db: Session = Depends(get_db_main)):
    employee = crud.get_employee_salary(db, emp_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@app.get('/calculate_bonus/{emp_id}')
def calculate_bonus(emp_id: int, db: Session = Depends(get_db_main)):
    bonus = crud.calculate_bonus(db, emp_id)
    if not bonus:
        raise HTTPException(status_code=404, detail="Employee not found")
    return bonus

@app.get('/list_employees')
def list_employees(db: Session = Depends(get_db_main)):
    employees = crud.list_employees(db)
    return {"employees": employees}

# @app.put('/update_salary/{emp_id}')
# def update_employee_salary(emp_id: int, salary_update: schemas.SalaryUpdate, db: Session = Depends(get_db_main)):
#     if salary_update.new_salary < 0:
#         raise HTTPException(status_code=400, detail="Salary cannot be negative")
#     return crud.update_salary(db, emp_id, salary_update.new_salary)

@app.put('/update_salary/{emp_id}')
def update_employee_salary(
    emp_id: int,
    salary_update: schemas.SalaryUpdate = Body(...),
    db: Session = Depends(get_db_main)
):
    if salary_update.new_salary < 0:
        raise HTTPException(status_code=400, detail="Salary cannot be negative")
    return crud.update_salary(db, emp_id, salary_update.new_salary)

@app.get('/get_salary_logs')
def fetch_salary_logs(db: Session = Depends(get_db_main)):
    return crud.get_salary_logs(db)

#To get updated salary employee with id
# @app.get('/get_salary_logs/{emp_id}')
# def fetch_salary_logs(emp_id: int, db: Session = Depends(get_db_main)):
#     return crud.get_salary_logs(db, emp_id)

@app.post('/add_employee')
def add_employee(employee: schemas.AddEmployee, db: Session = Depends(get_db_main)):
    if employee.emp_salary < 0:
        raise HTTPException(status_code=400, detail="Salary cannot be negative")
    return crud.add_employee(db, employee.emp_name, employee.emp_salary)

@app.post('/increase_all_salaries')
def increase_all_salaries(increase: schemas.SalaryIncrease, db: Session = Depends(get_db_main)):
    if increase.increase_percent< 0:
        raise HTTPException(status_code=400, detail="Increase percent cannot be negative")
    return crud.increase_all_salaries(db, increase.increase_percent)

@app.get("/testing", response_model=List[schemas.TestingSchema])
def read_testing(db: Session = Depends(get_db_main)):
    return crud.get_all_testing(db)


@app.get("/testingtwo", response_model=List[schemas.TestingTwoSchema])
def read_testingtwo(db: Session = Depends(get_db_main)):
    return crud.get_all_testingtwo(db)


@app.get("/insights", response_model=List[schemas.InsightsSchema])
def read_insights(db: Session = Depends(get_db_main)):
    return crud.get_all_insights(db)


@app.get("/communities", response_model=List[schemas.CommunitiesSchema])
def read_communities(db: Session = Depends(get_db_main)):
    return crud.get_all_communities(db)