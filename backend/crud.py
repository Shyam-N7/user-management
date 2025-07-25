from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from sqlalchemy.exc import DBAPIError
# from models import User
from schemas import UserCreate, UserResponse, UserUpdate, ClientCreate, ClientResponse, UserLogin, TestingSchema, TestingTwoSchema, InsightsSchema, CommunitiesSchema, StudentCreate, StudentResponse, StudentLogin, FacultyCreate, FacultyLogin, FacultyResponse
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from auth import hash_password, verify_password
def create_user(db: Session, user: UserCreate):
    query = text("SELECT id FROM users WHERE email = :email")
    result = db.execute(query, {"email": user.email})
    existing_user = result.mappings().first()

    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")
    
    query = text("INSERT INTO users (name, email) VALUES (:name, :email) RETURNING id, name, email")
    result = db.execute(query, {"name": user.name, "email": user.email})
    db.commit()
    user_res = result.mappings().first()
    if not user_res:
        raise HTTPException(status_code=500, detail="User creation failed")
    return UserResponse(**user_res)

#function to get user by id
def get_user(db: Session, user_id: int):
    #return db.query(User).filter(User.id == user_id).first() #returns first result
    
    #GET user using query
    query = text("SELECT id,name,email FROM users WHERE id = :id")
    result = db.execute(query, {"id": user_id})
    user_res = result.mappings().first()
    if not user_res:
        raise HTTPException(status_code=404, detail="Employee not found")
    return UserResponse(**user_res)

def get_all_users(db: Session):
    query = text("SELECT id, name, email FROM users")
    result = db.execute(query)
    users = result.mappings().all()
    return [UserResponse(**user) for user in users]

def update_user(db: Session, user_id: int, user: UserUpdate):
    query = text("UPDATE users SET name = COALESCE(:name, name), email = COALESCE(:email, email) WHERE id = :id RETURNING id, name, email")
    #use """ """ for multi line strings
    result = db.execute(query, {"id": user_id, "name": user.name, "email": user.email})
    db.commit()
    user_res = result.mappings().first()
    if not user_res:
        raise HTTPException(status_code=404, detail="Employee not found")
    return UserResponse(**user_res)

def delete_user(db: Session, user_id:int):
    query = text("DELETE FROM users WHERE id = :id RETURNING id, name, email")
    result = db.execute(query, {"id": user_id})
    db.commit()
    user_res = result.mappings().first()
    if not user_res:
        raise HTTPException(status_code=404, detail="Employee not found")
    return UserResponse(**user_res)


# CLIENTS LOGIN AND REGISTER

def create_client(db: Session, user: ClientCreate) -> ClientResponse:
    # CHECK EMAIL IF IT ALREADY EXISTS
    check_email = text("SELECT id FROM clients WHERE email = :email")
    try:
        check_email_result = db.execute(check_email, {"email": user.email}).first()
        if check_email_result:
            raise HTTPException(status_code=400, detail="Email already registered!") 
        
        # INSERT USER
        hashed_password = hash_password(user.password)
        query = text("""
            INSERT INTO clients (firstname, lastname, email, hashed_password)
            VALUES (:firstname, :lastname, :email, :hashed_password)
            RETURNING id, firstname, lastname, email
        """)
        result = db.execute(query, {
            "firstname": user.firstname,
            "lastname": user.lastname,
            "email": user.email,
            "hashed_password": hashed_password
        })
        db.commit()
        client_res = result.mappings().first()
        return ClientResponse(**client_res)
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    
def authenticate_client(db: Session, user: UserLogin) -> UserResponse:
    query = text("SELECT * FROM clients WHERE email = :email")
    try:
        result = db.execute(query, {"email": user.email}).mappings().first()
        if not result or not verify_password(user.password, result["hashed_password"]):
            return None
        return ClientResponse(id = result["id"], firstname = result["firstname"], lastname = result["lastname"], email = result["email"], detail = "Login Successful")
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    
def get_user_by_email(db: Session, email: str):
    query = text("SELECT id, firstname, lastname, email FROM clients WHERE email = :email")
    try:
        result = db.execute(query, {"email": email}).mappings().first()
        if result:
            return ClientResponse(id = result["id"], firstname = result["firstname"], lastname = result["lastname"], email = result["email"], detail = "User found by email")
        return None
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")

def store_password_reset_token(db: Session, user_id: int, token: str):
    # First, delete any existing reset tokens for this user
    delete_query = text("DELETE FROM password_reset_tokens WHERE user_id = :user_id")
    
    # Insert new reset token - using PostgreSQL's NOW() function
    insert_query = text("""
        INSERT INTO password_reset_tokens (user_id, token, created_at, expires_at)
        VALUES (:user_id, :token, NOW(), NOW() + INTERVAL '30 minutes')
    """)
    
    try:
        db.execute(delete_query, {"user_id": user_id})
        db.execute(insert_query, {
            "user_id": user_id,
            "token": token
        })
        db.commit()
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")

def verify_reset_token(db: Session, user_id: int, token: str):
    query = text("""
        SELECT id FROM password_reset_tokens 
        WHERE user_id = :user_id AND token = :token AND expires_at > NOW()
    """)
    
    try:
        result = db.execute(query, {
            "user_id": user_id,
            "token": token
        }).first()
        
        return result is not None
        
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")

def update_user_password(db: Session, user_id: int, new_password: str):
    hashed_password = hash_password(new_password)
    query = text("""
        UPDATE clients 
        SET hashed_password = :hashed_password, updated_at = NOW()
        WHERE id = :user_id
    """)
    
    try:
        db.execute(query, {
            "hashed_password": hashed_password,
            "user_id": user_id
        })
        db.commit()
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")

def delete_reset_token(db: Session, user_id: int, token: str):
    query = text("DELETE FROM password_reset_tokens WHERE user_id = :user_id AND token = :token")
    
    try:
        db.execute(query, {"user_id": user_id, "token": token})
        db.commit()
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")

def cleanup_expired_tokens(db: Session):
    query = text("DELETE FROM password_reset_tokens WHERE expires_at < NOW()")
    
    try:
        result = db.execute(query)
        db.commit()
        print(f"[CLEANUP] Removed {result.rowcount} expired password reset tokens")
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")

def get_square(db: Session, number:int):
    query = text("SELECT square(:number)")
    result = db.execute(query, {"number": number})
    square = result.mappings().first()
    if not square:  
        raise HTTPException(status_code=400, detail="Invalid input or function failed")
    return {"square": square["square"]}

def add_number(db: Session, a: int, b: int):
    query = text("SELECT add_numbers(:a, :b)")
    result = db.execute(query, {"a": a, "b": b})
    sum_result = result.mappings().first()
    if not sum_result:  
        raise HTTPException(status_code=400, detail="Invalid input or function failed")
    return {"sum": sum_result["add_numbers"]}

def celsius_to_farenheit(db: Session, celsius:float):

    if not isinstance(celsius, (int, float)):
        raise HTTPException(status_code=400, detail="Invalid input type. Celsius must be a number")
    
    query = text("SELECT celsius_to_farenheit(:celsius)")
    result = db.execute(query, {"celsius": celsius})
    farenheit = result.mappings().first()
    if not farenheit:  
        raise HTTPException(status_code=400, detail="Invalid input or function failed")
    return {"farenheit": farenheit["celsius_to_farenheit"]}

def check_even_odd(db: Session, number: int):
    query = text("SELECT check_even_odd(:number)")
    result = db.execute(query, {"number": number})
    even_odd = result.mappings().first()
    if not even_odd:  
        raise HTTPException(status_code=400, detail="Invalid input or function failed")
    return {"result": even_odd["check_even_odd"]}

def get_high_salary_employees(db: Session, salary_threshold: int):
    query = text("SELECT * FROM get_high_salary_employees(:salary_threshold)")
    result = db.execute(query, {"salary_threshold": salary_threshold})
    return result.mappings().all()

def get_employee_salary(db: Session, emp_id: int):
    query = text("SELECT * FROM get_employee_salary(:emp_id)")
    # result = db.execute(query, {"emp_id": emp_id})
    # employee = result.mappings().first()
    # if not employee or employee["amp_name"] is None:
    #     raise HTTPException(status_code=404, detail="Employee not found")
    # return {"name": employee["amp_name"], "salary": employee["emp_salary"]} 
    
    try:
        result = db.execute(query, {"emp_id": emp_id})
        employee = result.mappings().first()

        return {"name": employee["amp_name"], "salary": employee["emp_salary"]}

    except DBAPIError as e:
        # Extract PostgreSQL error message
        orig = e.orig
        if orig:
            raise HTTPException(status_code=404, detail=str(orig))
        raise HTTPException(status_code=500, detail="Database error occurred")
    
def calculate_bonus(db: Session, emp_id: int):
    query = text("SELECT * FROM calculate_bonus(:emp_id)")
    try: 
        result = db.execute(query, {"emp_id": emp_id})
        bonus = result.mappings().first()
        if not bonus:  
            raise HTTPException(status_code=404, detail="Employee not found")
        return {"name": bonus["emp_name"], "bonus": bonus["emp_bonus"]}

    except DBAPIError as e:
        # Extract PostgreSQL error message
        orig = e.orig
        if orig:
            raise HTTPException(status_code=404, detail=str(orig))
        raise HTTPException(status_code=500, detail="Database error occurred")
    
def list_employees(db: Session):
    query = text("SELECT * FROM list_employees()")
    try:
        result = db.execute(query)
        employees = result.mappings().all()
        return employees
    except DBAPIError as e:
        # Extract PostgreSQL error message
        orig = e.orig
        if orig:
            raise HTTPException(status_code=400, detail=str(orig))
        raise HTTPException(status_code=500, detail="Database error occurred")
    
def update_salary(db: Session, emp_id: int, new_salary: int):
    query = text("UPDATE employees SET salary = :new_salary WHERE id = :emp_id RETURNING id, salary")
    result = db.execute(query, {"new_salary": new_salary, "emp_id": emp_id})
    updated_emp = result.fetchone()
    db.commit() 
    
    if not updated_emp:
        db.rollback()
        raise HTTPException(status_code=404, detail=f"Employee with id {emp_id} not found")
    return {"message": "salary updated successfully", "emp_id": emp_id, "new_salary": new_salary}

def get_salary_logs(db: Session): #, emp_id: int
    query = text("SELECT * FROM salary_log") # WHERE emp_id = :emp_id
    try:
        result = db.execute(query) #, {"emp_id": emp_id}
        logs = result.mappings().all()
        
        if not logs:
            raise HTTPException(status_code=404, detail=f"No salary logs found")
        return logs
    
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    
def add_employee(db: Session, emp_name: str, emp_salary: int):
    query = text("CALL add_employee(:emp_name, :emp_salary)")
    try:
        db.execute(query, {"emp_name": emp_name, "emp_salary": emp_salary})
        db.commit()
        return {"message": "Employee added successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    
def increase_all_salaries(db: Session, increase_percent: int):
    query = text("CALL increase_all_salaries(:increase_percent)")
    try:
        db.execute(query, {"increase_percent": increase_percent})
        db.commit()
        return {"message": f"All employees salaries were increased by {increase_percent}%"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    
    
# Get all records from `testing` table
def get_all_testing(db: Session):
    query = text("SELECT id, img_url, name, role, email FROM testing")
    result = db.execute(query)
    records = result.mappings().all()
    return [TestingSchema(**row) for row in records]


# Get all records from `testingtwo` table
def get_all_testingtwo(db: Session):
    query = text("SELECT id, img_url, name, date, time, location, request, role FROM testingtwo")
    result = db.execute(query)
    records = result.mappings().all()
    return [TestingTwoSchema(**row) for row in records]


# Get all records from `insights` table
def get_all_insights(db: Session):
    query = text("SELECT id, heading, subheading FROM insights")
    result = db.execute(query)
    records = result.mappings().all()
    return [InsightsSchema(**row) for row in records]


# Get all records from `communities` table
def get_all_communities(db: Session):
    query = text("SELECT id, name, logo, privacy, members, date, notification FROM communities")
    result = db.execute(query)
    records = result.mappings().all()
    return [CommunitiesSchema(**row) for row in records]


# FOR CHARAIVETI

def create_student(db: Session, student: StudentCreate) -> StudentResponse:
    # CHECK EMAIL IF IT ALREADY EXISTS
    check_email = text("SELECT id FROM students WHERE email = :email")
    try:
        check_email_result = db.execute(check_email, {"email": student.email}).first()
        if check_email_result:
            raise HTTPException(status_code=400, detail="Email already registered!") 
        
        # INSERT USER
        hashed_password = hash_password(student.password)
        query = text("""
            INSERT INTO students (name, usn, email, hashed_password)
            VALUES (:name, :usn, :email, :hashed_password)
            RETURNING id, name, usn, email
        """)
        result = db.execute(query, {
            "name": student.name,
            "usn": student.usn,
            "email": student.email,
            "hashed_password": hashed_password
        })
        db.commit()
        student_res = result.mappings().first()
        return StudentResponse(**student_res)
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    
def authenticate_student(db: Session, student: StudentLogin) -> StudentResponse:
    query = text("SELECT * FROM students WHERE email = :email")
    try:
        result = db.execute(query, {"email": student.email}).mappings().first()
        if not result or not verify_password(student.password, result["hashed_password"]):
            raise HTTPException(status_code = 401, detail = "Invalid email or password")
        return StudentResponse(id = result["id"], name = result["name"], usn = result["usn"], email = result["email"], detail = "Login Successful")
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")

def create_faculty(db: Session, faculty: FacultyCreate) -> FacultyResponse:
    # CHECK EMAIL IF IT ALREADY EXISTS
    check_email = text("SELECT id FROM faculties WHERE email = :email")
    try:
        check_email_result = db.execute(check_email, {"email": faculty.email}).first()
        if check_email_result:
            raise HTTPException(status_code=400, detail="Email already registered!") 
        
        # INSERT USER
        hashed_password = hash_password(faculty.password)
        query = text("""
            INSERT INTO faculties (name, email, hashed_password)
            VALUES (:name, :email, :hashed_password)
            RETURNING id, name, email
        """)
        result = db.execute(query, {
            "name": faculty.name,
            "email": faculty.email,
            "hashed_password": hashed_password
        })
        db.commit()
        faculty_res = result.mappings().first()
        return FacultyResponse(**faculty_res)
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    
def authenticate_faculty(db: Session, faculty: FacultyLogin) -> FacultyResponse:
    query = text("SELECT * FROM faculties WHERE email = :email")
    try:
        result = db.execute(query, {"email": faculty.email}).mappings().first()
        if not result or not verify_password(faculty.password, result["hashed_password"]):
            raise HTTPException(status_code = 401, detail = "Invalid email or password")
        return FacultyResponse(id = result["id"], name = result["name"], email = result["email"], detail = "Login Successful")
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")