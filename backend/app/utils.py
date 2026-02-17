from app.database import SessionLocal
from app.models import User
from app.auth import hash_password

def create_user(email: str, password: str):
    db = SessionLocal()
    try:
        user = User(email=email, password=hash_password(password))
        db.add(user)
        db.commit()
        print(f"User {email} created successfully!")
    except Exception as e:
        print("Error creating user:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Change these to whatever you want
    create_user("admin@example.com", "admin123")
