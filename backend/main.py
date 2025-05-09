from fastapi import FastAPI, Depends, HTTPException
#Depends allows to pass dependencies
from sqlalchemy.orm import Session
import models, schemas, crud
from database import engine
from dependencies import get_db
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

#Create db tables if they don't exist
models.Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI!"}

@app.post("/users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    user = crud.create_user(db=db, user=user)
    return user

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get('/users', response_model=list[schemas.UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    users = crud.get_all_users(db)
    return users

@app.put('/users/{user_id}', response_model=schemas.UserResponse)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    updated_user = crud.update_user(db, user_id, user)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@app.delete('/users/{user_id}', response_model=dict)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    deleted_user = crud.delete_user(db, user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully", "user": deleted_user}


@app.get('/square/{number}')
def get_square(number: int, db: Session = Depends(get_db)):
    return crud.get_square(db, number)

@app.post('/add_numbers')
def add_numbers(num: schemas.AddNumbers, db:Session = Depends(get_db)):
    return crud.add_number(db, num.a, num.b)

@app.post('/celsius_to_fahrenheit')
def celsius_to_fahrenheit(temperature: schemas.ToFarenheit, db: Session = Depends(get_db)):
    return crud.celsius_to_farenheit(db, temperature.celsius)

@app.get('/check_even_odd/{number}')
def check_even_odd(number: int, db: Session = Depends(get_db)):
    return crud.check_even_odd(db, number)

@app.get('/high_salary_employees/{salary_threshold}')
def high_salary_employees(salary_threshold: int, db: Session = Depends(get_db)):
    return crud.get_high_salary_employees(db, salary_threshold)

@app.get('/get_employee_salary/{emp_id}')
def get_employee_salary(emp_id: int, db: Session = Depends(get_db)):
    employee = crud.get_employee_salary(db, emp_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@app.get('/calculate_bonus/{emp_id}')
def calculate_bonus(emp_id: int, db: Session = Depends(get_db)):
    bonus = crud.calculate_bonus(db, emp_id)
    if not bonus:
        raise HTTPException(status_code=404, detail="Employee not found")
    return bonus

@app.get('/list_employees')
def list_employees(db: Session = Depends(get_db)):
    employees = crud.list_employees(db)
    return {"employees": employees}

# @app.put('/update_salary/{emp_id}')
# def update_employee_salary(emp_id: int, salary_update: schemas.SalaryUpdate, db: Session = Depends(get_db)):
#     if salary_update.new_salary < 0:
#         raise HTTPException(status_code=400, detail="Salary cannot be negative")
#     return crud.update_salary(db, emp_id, salary_update.new_salary)

@app.put('/update_salary/{emp_id}')
def update_employee_salary(
    emp_id: int,
    salary_update: schemas.SalaryUpdate = Body(...),
    db: Session = Depends(get_db)
):
    if salary_update.new_salary < 0:
        raise HTTPException(status_code=400, detail="Salary cannot be negative")
    return crud.update_salary(db, emp_id, salary_update.new_salary)

@app.get('/get_salary_logs')
def fetch_salary_logs(db: Session = Depends(get_db)):
    return crud.get_salary_logs(db)

#To get updated salary employee with id
# @app.get('/get_salary_logs/{emp_id}')
# def fetch_salary_logs(emp_id: int, db: Session = Depends(get_db)):
#     return crud.get_salary_logs(db, emp_id)

@app.post('/add_employee')
def add_employee(employee: schemas.AddEmployee, db: Session = Depends(get_db)):
    if employee.emp_salary < 0:
        raise HTTPException(status_code=400, detail="Salary cannot be negative")
    return crud.add_employee(db, employee.emp_name, employee.emp_salary)

@app.post('/increase_all_salaries')
def increase_all_salaries(increase: schemas.SalaryIncrease, db: Session = Depends(get_db)):
    if increase.increase_percent< 0:
        raise HTTPException(status_code=400, detail="Increase percent cannot be negative")
    return crud.increase_all_salaries(db, increase.increase_percent)