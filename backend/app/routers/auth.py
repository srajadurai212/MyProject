from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import verify_password, hash_password
from app.schemas import RegisterSchema, LoginSchema

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create user
    hashed_password = hash_password(data.password)
    user = User(email=data.email, password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully", "email": user.email}
