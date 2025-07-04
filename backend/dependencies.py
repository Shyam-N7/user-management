from database import SessionLocalMain, SessionLocalUsers, SessionLocalStudents

def get_db_main():
    db_main = SessionLocalMain()
    #provides db session for api routes
    try:
        yield db_main
    #Terminates session after completion
    finally:
        db_main.close()
        
def get_db_users():
    db_users = SessionLocalUsers()
    #provides db session for api routes
    try:
        yield db_users
    #Terminates session after completion
    finally:
        db_users.close()
        
def get_db_students():
    db_students = SessionLocalStudents()
    #provides db session for api routes
    try:
        yield db_students
    #Terminates session after completion
    finally:
        db_students.close()