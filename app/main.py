from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.routes.auth import router as auth_router
from app.routes.password_reset import router as password_reset_router
from app.routes.interview import router as interview_router

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
    return {"message": "API is running"}

app.include_router(auth_router)
app.include_router(password_reset_router)
app.include_router(interview_router)