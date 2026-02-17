from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import fetch_data
import pandas as pd
from app.auth_guard import get_current_user

router = APIRouter(prefix="/historical", tags=["Historical"])

@router.get("/")
def get_historical_data(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user)
):
    df = fetch_data(db, "historical_data", start_date, end_date)

    if df.empty:
        return {"message": "No data available"}

    return df[["date", "hrc_price"]].rename(
        columns={"hrc_price": "flat_steel_price"}
    ).to_dict(orient="records")
# def fetch_original_data(db: Session, start_date: str, end_date: str):
#     query = f"""
#         SELECT *
#         FROM "Original_Data"
#         WHERE "Date" BETWEEN '{start_date}' AND '{end_date}'
#         ORDER BY "Date"
#     """
#     df = pd.read_sql(query, db.bind)  # db.bind gives SQLAlchemy engine
#     return df


# @router.get("/")
# def get_historical_data(
#     start_date: str,
#     end_date: str,
#     db: Session = Depends(get_db)
# ):
#     df = fetch_original_data(db, start_date, end_date)

#     if df.empty:
#         return {"message": "No data available"}

#     # Rename only the target column for frontend
#     # df = df.rename(columns={"Hot_Rolled_Coil_Futures": "flat_steel_price"})

#     # Convert all data to dictionary for JSON response
#     return df.to_dict(orient="records")