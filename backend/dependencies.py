from database import SessionLocal

def get_db():
    db = SessionLocal()
    #provides db session for api routes
    try:
        yield db
    #Terminates session after completion
    finally:
        db.close()