from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from app.routes.auth import router as auth_router

app = FastAPI(title="stack-from-scratch-backend")


@app.get("/")
def root():
    print("API is Running")
    return {"message": "API is running"}


app.include_router(auth_router)