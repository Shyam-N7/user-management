from fastapi import FastAPI, Depends, HTTPException, Request
#Depends allows to pass dependencies
from sqlalchemy.orm import Session
import models, schemas, crud
from database import engine_main, engine_users
from dependencies import get_db_main, get_db_users, get_db_students
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
import json
from auth import create_access_token
from typing import List
import logging
import re
from collections import defaultdict
from typing import Optional
import time
import hashlib
from datetime import datetime
from auth import (create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES)
from middleware.blacklist_token import TokenBlocklistMiddleware
from routes.user import user_router
from routes.students import student_router
from routes.faculties import faculty_router
import rate_limit
from redis_connxn import r

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

app.add_middleware(TokenBlocklistMiddleware)

app.include_router(user_router, prefix="/api")
app.include_router(student_router, prefix="/api")
app.include_router(faculty_router, prefix="/api")

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
    print(f"[LOGIN] Starting login for IP: {client_ip}")
    
    try:
        print(f"[LOGIN] Checking rate limit for IP: {client_ip}")
        rate_limit.check_client_rate_limit(client_ip, r)
        print(f"[LOGIN] Rate limit check passed for IP: {client_ip}")
        
        if not user.email or not user.password:
            print(f"[LOGIN] Missing credentials for IP: {client_ip}")
            rate_limit.record_client_failed_attempt(client_ip, r)
            remaining = rate_limit.get_client_remaining_attempts(client_ip, r)
            raise HTTPException(
                status_code=400,
                detail=f"Email and password are required. {remaining} attempts remaining."
            )
        
        sanitized_email = sanitize_input(user.email.lower())
        sanitized_password = sanitize_input(user.password)
        
        if not validate_email(sanitized_email):
            print(f"[LOGIN] Invalid email format for IP: {client_ip}")
            rate_limit.record_client_failed_attempt(client_ip, r)
            remaining = rate_limit.get_client_remaining_attempts(client_ip, r)
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid email format. {remaining} attempts remaining."
            )
        
        print(f"[LOGIN] Email validation passed, attempting authentication")
        
        sanitized_user = schemas.UserLogin(
            email=sanitized_email,
            password=sanitized_password
        )
        
        try:
            authenticated = crud.authenticate_client(db, sanitized_user)
            print(f"[LOGIN] Authentication successful: {authenticated}")
            
        except HTTPException as auth_error:
            print(f"[LOGIN] Authentication failed for IP: {client_ip} - {auth_error.detail}")
            rate_limit.record_client_failed_attempt(client_ip, r)
            remaining = rate_limit.get_client_remaining_attempts(client_ip, r)
            
            raise HTTPException(
                status_code=401,
                detail=f"Invalid email or password. {remaining} attempts remaining."
            )
        
        if not authenticated:
            print(f"[LOGIN] Authentication returned False for IP: {client_ip}")
            rate_limit.record_client_failed_attempt(client_ip, r)
            remaining = rate_limit.get_client_remaining_attempts(client_ip, r)
            
            raise HTTPException(
                status_code=401,
                detail=f"Invalid email or password. {remaining} attempts remaining."
            )
        
        print(f"[LOGIN] Authentication successful for IP: {client_ip}")
        rate_limit.reset_failed_attempts(client_ip, r)
        
        access_token = create_access_token(data={"sub": authenticated.id})
        
        response = JSONResponse(content={
            "message": authenticated.detail,
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": authenticated.id,
                "firstname": authenticated.firstname,
                "lastname": authenticated.lastname,
                "email": authenticated.email
            },
            "login_timestamp": datetime.now().isoformat(),
            "success": True
        })
        
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        response.set_cookie(
            key="user",
            value=json.dumps({
                "id": authenticated.id,
                "firstname": authenticated.firstname,
                "lastname": authenticated.lastname,
                "email": authenticated.email
            }),
            httponly=False,
            path="/",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        return response
    
    except HTTPException as he:
        if he.status_code == 429:
            print(f"[LOGIN] Rate limit exceeded for IP: {client_ip}")
        else:
            print(f"[LOGIN] HTTPException caught: {he.detail}")
        raise  # Re-raise the HTTPException
        
    except Exception as e:
        print(f"[LOGIN] Unexpected error for IP: {client_ip}: {e}")
        rate_limit.record_failed_attempt_redis(client_ip, r)
        remaining = rate_limit.get_remaining_attempts(client_ip, r)
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error. {remaining} attempts remaining."
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


# FOR CHARAIVETI

def validate_usn_field(usn: str, field_name: str) -> bool:
    if not usn or len(usn.strip()) == 0:
        return False
    
    if len(usn) > 40:
        return False

    pattern = r'^[a-zA-Z0-9]+$'
    return re.match(pattern, usn) is not None

def sanitize_usn(input_string: str) -> str:
    if not input_string:
        return ""
    
    sanitized = re.sub(r'[^a-zA-Z0-9]', '', input_string)
    return sanitized

@app.post('/students-register', response_model=schemas.StudentResponse)
def register(student: schemas.StudentCreate, request: Request, db: Session = Depends(get_db_students)):
    
    student_ip = get_client_ip(request)
    
    is_limited, limit_message = is_rate_limited(student_ip)
    if is_limited:
        logger.warning(f"Registration rate limit exceeded for IP: {student_ip}")
        raise HTTPException(status_code=429, detail=limit_message)
    
    try:
        if not student.email or not student.password or not student.name or not student.usn:
            logger.warning(f"Registration attempt with missing fields from IP: {student_ip}")
            raise HTTPException(
                status_code=400,
                detail="All fields (firstname, lastname, email, password) are required"
            )
        
        sanitized_name = sanitize_input(student.name)
        sanitized_usn = sanitize_usn(student.usn)
        sanitized_email = sanitize_input(student.email.lower())
        sanitized_password = sanitize_input(student.password)
        
        if not validate_email(sanitized_email):
            logger.warning(f"Invalid email format in registration from IP: {student_ip}")
            record_failed_attempt(student_ip)  # Count as failed attempt
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        if not validate_name_field(sanitized_name, "Name"):
            record_failed_attempt(student_ip)
            raise HTTPException(status_code=400, detail="Invalid name")
            
        if not validate_usn_field(sanitized_usn, "Usn"):
            record_failed_attempt(student_ip)
            raise HTTPException(status_code=400, detail="Invalid usn")
        
        if not validate_password_strength(sanitized_password):
            record_failed_attempt(student_ip)
            raise HTTPException(
                status_code=400, 
                detail="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
            )
        
        logger.info(f"Registration attempt for email hash: {hash_sensitive_data(sanitized_email)} from IP: {student_ip}")
        
        sanitized_student = schemas.StudentCreate(
            name=sanitized_name,
            usn=sanitized_usn,
            email=sanitized_email,
            password=sanitized_password
        )
        
        new_student = crud.create_student(db, sanitized_student)
        
        logger.info(f"Successful registration for user ID: {new_student.id} from IP: {student_ip}")
        
        if student_ip in login_attempts:
            login_attempts[student_ip] = []
        
        return new_student
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected registration error for IP: {student_ip}, Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred during registration"
        )

@app.post('/students-login')
def login(user: schemas.StudentLogin, request: Request, db: Session = Depends(get_db_students)):
    
    student_ip = get_client_ip(request)
    print(f"[STUDENT-LOGIN] Starting login for IP: {student_ip}")
    
    try:
        print(f"[STUDENT-LOGIN] Checking rate limit for IP: {student_ip}")
        
        is_limited, limit_message = is_rate_limited(student_ip)
        if is_limited:
            print(f"[STUDENT-LOGIN] Rate limit exceeded for IP: {student_ip}")
            logger.warning(f"Rate limit exceeded for IP: {student_ip}")
            raise HTTPException(status_code=429, detail=limit_message)
        
        print(f"[STUDENT-LOGIN] Rate limit check passed for IP: {student_ip}")
        
        if not user.email or not user.password:
            print(f"[STUDENT-LOGIN] Missing credentials for IP: {student_ip}")
            logger.warning(f"Login attempt with missing credentials from IP: {student_ip}")
            rate_limit.record_student_failed_attempt(student_ip, r)
            remaining_attempts = rate_limit.get_student_remaining_attempts(student_ip, r)  # You may need to implement this
            raise HTTPException(
                status_code=400,
                detail=f"Email and password are required. {remaining_attempts} attempts remaining."
            )
        
        sanitized_email = sanitize_input(user.email.lower())
        sanitized_password = sanitize_input(user.password)
        
        if not validate_email(sanitized_email):
            print(f"[STUDENT-LOGIN] Invalid email format for IP: {student_ip}")
            logger.warning(f"Invalid email format attempted from IP: {student_ip}")
            rate_limit.record_student_failed_attempt(student_ip, r)
            remaining_attempts = rate_limit.get_student_remaining_attempts(student_ip, r)
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid email format. {remaining_attempts} attempts remaining."
            )
        
        print(f"[STUDENT-LOGIN] Email validation passed, attempting authentication")
        logger.info(f"Login attempt for email hash: {hash_sensitive_data(sanitized_email)} from IP: {student_ip}")
        
        sanitized_student = schemas.StudentLogin(
            email=sanitized_email,
            password=sanitized_password
        )
        
        try:
            authenticated = crud.authenticate_student(db, sanitized_student)
            print(f"[STUDENT-LOGIN] Authentication successful: {authenticated}")
            
        except HTTPException as auth_error:
            print(f"[STUDENT-LOGIN] Authentication failed for IP: {student_ip} - {auth_error.detail}")
            rate_limit.record_student_failed_attempt(student_ip, r)
            remaining_attempts = rate_limit.get_student_remaining_attempts(student_ip, r)
            logger.warning(
                f"Failed login attempt for email hash: {hash_sensitive_data(sanitized_email)} "
                f"from IP: {student_ip}"
            )
            
            raise HTTPException(
                status_code=401,
                detail=f"Invalid email or password. {remaining_attempts} attempts remaining."
            )
        
        if not authenticated:
            print(f"[STUDENT-LOGIN] Authentication returned False for IP: {student_ip}")
            rate_limit.record_student_failed_attempt(student_ip, r)
            remaining_attempts = rate_limit.get_student_remaining_attempts(student_ip, r)
            logger.warning(
                f"Failed login attempt for email hash: {hash_sensitive_data(sanitized_email)} "
                f"from IP: {student_ip}"
            )
            
            raise HTTPException(
                status_code=401,
                detail=f"Invalid email or password. {remaining_attempts} attempts remaining."
            )
        
        print(f"[LOGIN] Authentication successful for IP: {student_ip}")
        rate_limit.reset_failed_attempts(student_ip, r)
        
        if student_ip in login_attempts:
            login_attempts[student_ip] = []
            
        
        access_token = create_access_token(data={"sub": authenticated.id})
        
        response = JSONResponse(content={
            "message": authenticated.detail,
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": authenticated.id,
                "name": authenticated.name,
                "email": authenticated.email
            },
            "login_timestamp": datetime.now().isoformat(),
            "success": True
        })
        
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        response.set_cookie(
            key="user",
            value=json.dumps({
                "id": authenticated.id,
                "name": authenticated.name,
                "email": authenticated.email
            }),
            httponly=False,
            path="/",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        return response
    
    except HTTPException as he:
        if he.status_code == 429:
            print(f"[STUDENT-LOGIN] Rate limit exceeded for IP: {student_ip}")
        else:
            print(f"[STUDENT-LOGIN] HTTPException caught: {he.detail}")
        raise  # Re-raise the HTTPException
        
    except Exception as e:
        print(f"[STUDENT-LOGIN] Unexpected error for IP: {student_ip}: {e}")
        logger.error(f"Unexpected login error for IP: {student_ip}, Error: {str(e)}", exc_info=True)
        rate_limit.record_student_failed_attempt(student_ip, r)
        remaining_attempts = rate_limit.get_student_remaining_attempts(student_ip, r)
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error. {remaining_attempts} attempts remaining."
        )

@app.post('/faculty-register', response_model=schemas.FacultyResponse)
def register(faculty: schemas.FacultyCreate, request: Request, db: Session = Depends(get_db_students)):
    
    faculty_ip = get_client_ip(request)
    
    is_limited, limit_message = is_rate_limited(faculty_ip)
    if is_limited:
        logger.warning(f"Registration rate limit exceeded for IP: {faculty_ip}")
        raise HTTPException(status_code=429, detail=limit_message)
    
    try:
        if not faculty.email or not faculty.password or not faculty.name:
            logger.warning(f"Registration attempt with missing fields from IP: {faculty_ip}")
            raise HTTPException(
                status_code=400,
                detail="All fields (firstname, lastname, email, password) are required"
            )
        
        sanitized_name = sanitize_input(faculty.name)
        sanitized_email = sanitize_input(faculty.email.lower())
        sanitized_password = sanitize_input(faculty.password)
        
        if not validate_email(sanitized_email):
            logger.warning(f"Invalid email format in registration from IP: {faculty_ip}")
            record_failed_attempt(faculty_ip)  # Count as failed attempt
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        if not validate_name_field(sanitized_name, "Name"):
            record_failed_attempt(faculty_ip)
            raise HTTPException(status_code=400, detail="Invalid name")
        
        if not validate_password_strength(sanitized_password):
            record_failed_attempt(faculty_ip)
            raise HTTPException(
                status_code=400, 
                detail="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
            )
        
        logger.info(f"Registration attempt for email hash: {hash_sensitive_data(sanitized_email)} from IP: {faculty_ip}")
        
        sanitized_faculty = schemas.FacultyCreate(
            name=sanitized_name,
            email=sanitized_email,
            password=sanitized_password
        )
        
        new_faculty = crud.create_faculty(db, sanitized_faculty)
        
        logger.info(f"Successful registration for user ID: {new_faculty.id} from IP: {faculty_ip}")
        
        if faculty_ip in login_attempts:
            login_attempts[faculty_ip] = []
        
        return new_faculty
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected registration error for IP: {faculty_ip}, Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred during registration"
        )


@app.post('/faculty-login')
def login(user: schemas.FacultyLogin, request: Request, db: Session = Depends(get_db_students)):
    
    faculty_ip = get_client_ip(request)
    print(f"[FACULTY-LOGIN] Starting login for IP: {faculty_ip}")
    
    try:
        print(f"[FACULTY-LOGIN] Checking rate limit for IP: {faculty_ip}")
        
        rate_limit.check_faculty_rate_limit(faculty_ip, r)
        print(f"[FACULTY-LOGIN] Rate limit check passed for IP: {faculty_ip}")
        
        if not user.email or not user.password:
            print(f"[FACULTY-LOGIN] Missing credentials for IP: {faculty_ip}")
            logger.warning(f"Login attempt with missing credentials from IP: {faculty_ip}")
            rate_limit.record_faculty_failed_attempt(faculty_ip, r)
            remaining = rate_limit.get_faculty_remaining_attempts(faculty_ip, r)
            raise HTTPException(
                status_code=400,
                detail=f"Email and password are required. {remaining} attempts remaining."
            )
        
        sanitized_email = sanitize_input(user.email.lower())
        sanitized_password = sanitize_input(user.password)
        
        if not validate_email(sanitized_email):
            print(f"[FACULTY-LOGIN] Invalid email format for IP: {faculty_ip}")
            logger.warning(f"Invalid email format attempted from IP: {faculty_ip}")
            rate_limit.record_faculty_failed_attempt(faculty_ip, r)
            remaining = rate_limit.get_faculty_remaining_attempts(faculty_ip, r)
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid email format. {remaining} attempts remaining."
            )
        
        print(f"[FACULTY-LOGIN] Email validation passed, attempting authentication")
        logger.info(f"Login attempt for email hash: {hash_sensitive_data(sanitized_email)} from IP: {faculty_ip}")
        
        sanitized_faculty = schemas.FacultyLogin(
            email=sanitized_email,
            password=sanitized_password
        )
        
        try:
            authenticated = crud.authenticate_faculty(db, sanitized_faculty)
            print(f"[FACULTY-LOGIN] Authentication successful: {authenticated}")
            
        except HTTPException as auth_error:
            print(f"[FACULTY-LOGIN] Authentication failed for IP: {faculty_ip} - {auth_error.detail}")
            rate_limit.record_faculty_failed_attempt(faculty_ip, r)
            remaining = rate_limit.get_faculty_remaining_attempts(faculty_ip, r)
            logger.warning(
                f"Failed login attempt for email hash: {hash_sensitive_data(sanitized_email)} "
                f"from IP: {faculty_ip}"
            )
            
            raise HTTPException(
                status_code=401,
                detail=f"Invalid email or password. {remaining} attempts remaining."
            )
        
        if not authenticated:
            print(f"[FACULTY-LOGIN] Authentication returned False for IP: {faculty_ip}")
            rate_limit.record_faculty_failed_attempt(faculty_ip, r)
            remaining = rate_limit.get_faculty_remaining_attempts(faculty_ip, r)
            logger.warning(
                f"Failed login attempt for email hash: {hash_sensitive_data(sanitized_email)} "
                f"from IP: {faculty_ip}"
            )
            
            raise HTTPException(
                status_code=401,
                detail=f"Invalid email or password. {remaining} attempts remaining."
            )
        
        print(f"[LOGIN] Authentication successful for IP: {faculty_ip}")
        rate_limit.reset_failed_attempts(faculty_ip, r)
        
        access_token = create_access_token(data={"sub": authenticated.id})
        
        response = JSONResponse(content={
            "message": authenticated.detail,
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": authenticated.id,
                "name": authenticated.name,
                "email": authenticated.email
            },
            "login_timestamp": datetime.now().isoformat(),
            "success": True
        })
        
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="Lax",
            path="/",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        response.set_cookie(
            key="user",
            value=json.dumps({
                "id": authenticated.id,
                "name": authenticated.name,
                "email": authenticated.email
            }),
            httponly=False,
            path="/",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        return response
    
    except HTTPException as he:
        if he.status_code == 429:
            print(f"[FACULTY-LOGIN] Rate limit exceeded for IP: {faculty_ip}")
        else:
            print(f"[FACULTY-LOGIN] HTTPException caught: {he.detail}")
        raise  # Re-raise the HTTPException
        
    except Exception as e:
        print(f"[FACULTY-LOGIN] Unexpected error for IP: {faculty_ip}: {e}")
        logger.error(f"Unexpected login error for IP: {faculty_ip}, Error: {str(e)}", exc_info=True)
        rate_limit.record_faculty_failed_attempt(faculty_ip, r)
        remaining = rate_limit.get_faculty_remaining_attempts(faculty_ip, r)
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error. {remaining} attempts remaining."
        )

@app.get('/debug/rate-limit/{ip}')
def debug_rate_limit(ip: str):
    from rate_limit import get_rate_limit_info
    return get_rate_limit_info(ip, r)

@app.post('/test/rate-limit')
def test_rate_limit(request: Request):
    client_ip = get_client_ip(request)
    
    try:
        from rate_limit import get_rate_limit_info
        before = get_rate_limit_info(client_ip, r)
        print(f"[TEST] Before: {before}")
        
        # FIXED: Call without redis_client parameter
        rate_limit.record_failed_attempt_redis(client_ip, r)
        
        after = get_rate_limit_info(client_ip, r)
        print(f"[TEST] After: {after}")
        
        return {
            "message": "Rate limit test completed",
            "before": before,
            "after": after
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Rate limit test failed"
        }

@app.post('/test/reset-rate-limit')  
def reset_rate_limit_test(request: Request):
    client_ip = get_client_ip(request)
    rate_limit.reset_failed_attempts(client_ip, r)
    
    from rate_limit import get_rate_limit_info
    info = get_rate_limit_info(client_ip, r)
    
    return {
        "message": f"Rate limit reset for IP: {client_ip}",
        "info": info
    }
    
@app.get('/debugstudent/rate-limit/{ip}')
def debug_rate_limit(ip: str):
    from rate_limit import get_rate_limit_info
    return get_rate_limit_info(ip, r)

@app.post('/teststudent/rate-limit')
def test_rate_limit(request: Request):
    student_ip = get_client_ip(request)
    
    try:
        from rate_limit import get_rate_limit_info
        before = get_rate_limit_info(student_ip, r)
        print(f"[TEST] Before: {before}")
        
        # FIXED: Call without redis_client parameter
        rate_limit.record_failed_attempt_redis(student_ip, r)
        
        after = get_rate_limit_info(student_ip, r)
        print(f"[TEST] After: {after}")
        
        return {
            "message": "Rate limit test completed",
            "before": before,
            "after": after
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Rate limit test failed"
        }

@app.post('/teststudent/reset-rate-limit')  
def reset_rate_limit_test(request: Request):
    student_ip = get_client_ip(request)
    rate_limit.reset_failed_attempts(student_ip, r)
    
    from rate_limit import get_rate_limit_info
    info = get_rate_limit_info(student_ip, r)
    
    return {
        "message": f"Rate limit reset for IP: {student_ip}",
        "info": info
    }
    
@app.get('/debugfaculty/rate-limit/{ip}')
def debug_rate_limit(ip: str):
    from rate_limit import get_rate_limit_info
    return get_rate_limit_info(ip, r)

@app.post('/testfaculty/rate-limit')
def test_rate_limit(request: Request):
    faculty_ip = get_client_ip(request)
    
    try:
        from rate_limit import get_rate_limit_info
        before = get_rate_limit_info(faculty_ip, r)
        print(f"[TEST] Before: {before}")
        
        # FIXED: Call without redis_client parameter
        rate_limit.record_failed_attempt_redis(faculty_ip, r)
        
        after = get_rate_limit_info(faculty_ip, r)
        print(f"[TEST] After: {after}")
        
        return {
            "message": "Rate limit test completed",
            "before": before,
            "after": after
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Rate limit test failed"
        }

@app.post('/testfaculty/reset-rate-limit')  
def reset_rate_limit_test(request: Request):
    faculty_ip = get_client_ip(request)
    rate_limit.reset_failed_attempts(faculty_ip, r)
    
    from rate_limit import get_rate_limit_info
    info = get_rate_limit_info(faculty_ip, r)
    
    return {
        "message": f"Rate limit reset for IP: {faculty_ip}",
        "info": info
    }