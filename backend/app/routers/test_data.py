from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import fetch_data
import numpy as np
from app.auth_guard import get_current_user

router = APIRouter(prefix="/test-data", tags=["Test Data"])

TEST_TABLES = {
    "v3": "test_data_v3",
    "v6": "test_data_v6",
    "v9": "test_data_v9",
}

@router.get("/")
def get_test_data(
    version: str,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user) 
):
    table = TEST_TABLES[version]
    df = fetch_data(db, table, start_date, end_date)

    if df.empty:
        return {"message": "No data available"}

    df["mape"] = abs(df["actual"] - df["predicted"]) / df["actual"] * 100
    df["accuracy"] = 100 - df["mape"]

    return df.rename(columns={
        "actual": "actual_price",
        "predicted": "predicted_price"
    })[["date", "actual_price", "predicted_price", "mape", "accuracy"]] \
        .to_dict(orient="records")
