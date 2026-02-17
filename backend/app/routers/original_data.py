from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import fetch_data
import pandas as pd
from app.auth_guard import get_current_user

router = APIRouter(prefix="/original", tags=["Original"])


def fetch_original_data(db: Session, start_date: str, end_date: str):
    query = f"""
        SELECT *
        FROM "Original_Data"
        WHERE "Date" BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY "Date"
    """
    df = pd.read_sql(query, db.bind)  # db.bind gives SQLAlchemy engine
    return df


@router.get("/")
def get_original_data(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    df = fetch_original_data(db, start_date, end_date)

    if df.empty:
        return {"message": "No data available"}

    # Rename only the target column for frontend
    # df = df.rename(columns={"Hot_Rolled_Coil_Futures": "flat_steel_price"})

    # Convert all data to dictionary for JSON response
    return df.to_dict(orient="records")