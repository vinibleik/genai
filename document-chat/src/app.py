from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from src.routers import api

app = FastAPI()
app.include_router(prefix="/api", router=api)


@app.get("/health-check")
def health_check():
    return {"health": "check"}
