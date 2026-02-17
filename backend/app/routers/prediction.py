from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import fetch_data
import numpy as np
from app.auth_guard import get_current_user

router = APIRouter(prefix="/prediction", tags=["Prediction"])

PREDICTION_TABLES = {
    "v3": "prediction_v3",
    "v6": "prediction_v6",
    "v9": "prediction_v9",
}

@router.get("/individual")
def individual_prediction(
    version: str = Query(..., enum=["v3", "v6", "v9"]),
    start_date: str = Query(...),
    end_date: str = Query(...),
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user) 
):
    table = PREDICTION_TABLES[version]
    df = fetch_data(db, table, start_date, end_date)

    if df.empty:
        return {"message": "No data available"}

    best_buy = df.loc[df["predicted"].idxmin()]

    return {
        "records": len(df),
        "best_buy": {
            "date": best_buy["date"],
            "price": round(best_buy["predicted"], 2)
        },
        "data": df[["date", "predicted"]].to_dict(orient="records")
    }


@router.get("/comparison")
def prediction_comparison(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user) 
):
    df_v3 = fetch_data(db, "prediction_v3", start_date, end_date)
    df_v6 = fetch_data(db, "prediction_v6", start_date, end_date)
    df_v9 = fetch_data(db, "prediction_v9", start_date, end_date)

    if df_v3.empty or df_v6.empty or df_v9.empty:
        return {"message": "Data missing for one or more versions"}

    df_v3 = df_v3.rename(columns={
        "predicted": "predicted_v3"
    })[["date", "predicted_v3"]]

    df_v6 = df_v6.rename(columns={
        "predicted": "predicted_v6"
    })[["date", "predicted_v6"]]

    df_v9 = df_v9.rename(columns={
        "predicted": "predicted_v9"
    })[["date", "predicted_v9"]]

    df = (
        df_v3
        .merge(df_v6, on="date", how="inner")
        .merge(df_v9, on="date", how="inner")
    )

    return df.to_dict(orient="records")

