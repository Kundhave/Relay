import time
from fastapi import FastAPI
from .database import engine, Base
from . import models  # noqa: F401 — must import to register models with Base.metadata

app = FastAPI()

@app.on_event("startup")
def startup_event():
    # Simple retry loop to wait for database to be ready
    retries = 5
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            break
        except Exception as e:
            print(f"Database connection failed, retrying... ({retries} left)")
            retries -= 1
            time.sleep(5)
    else:
        print("Could not connect to database. Exiting.")
        raise Exception("Database connection failed after retries")

@app.get("/")
async def health_check():
    return {"status": "ok", "service": "relay"}
