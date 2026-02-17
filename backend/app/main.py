import os
import sys
occt_bin = os.path.join(sys.prefix, "Library", "bin")
os.environ["PATH"] = occt_bin + os.pathsep + os.environ.get("PATH", "")

from fastapi import FastAPI
from app.routers import prediction, historical, test_data, cad, costing, dropdowns, original_data, login, auth, recommendations
from fastapi.middleware.cors import CORSMiddleware
import requests
from fastapi.staticfiles import StaticFiles
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

app = FastAPI(
    title="POCs",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(login.router)
app.include_router(prediction.router)
app.include_router(historical.router)
app.include_router(original_data.router)
app.include_router(test_data.router)
# app.include_router(benchmarking.router)
app.include_router(cad.router)
app.include_router(costing.router)
app.include_router(dropdowns.router)
app.include_router(recommendations.router)


def root():
    return {"message": "Poc API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)