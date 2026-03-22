from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.routes.auth import router as auth_router

app = FastAPI(title="stack-from-scratch-backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],        
)

@app.get("/")
def root():
    print("API is Running")
    return {"message": "API is running"}

app.include_router(auth_router)