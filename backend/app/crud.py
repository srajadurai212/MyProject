from sqlalchemy import text
import pandas as pd

def fetch_data(db, table: str, start_date, end_date):
    query = text(f"""
        SELECT *
        FROM {table}
        WHERE date BETWEEN :start_date AND :end_date
        ORDER BY date
    """)
    result = db.execute(query, {
        "start_date": start_date,
        "end_date": end_date
    })
    return pd.DataFrame(result.fetchall(), columns=result.keys())
