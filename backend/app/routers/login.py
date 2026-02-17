from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.schemas import LoginSchema
from app.models import User
from app.auth import verify_password, create_access_token

router = APIRouter(prefix="/login", tags=["login"])

@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer"
    }
