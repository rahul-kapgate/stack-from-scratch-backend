from fastapi import FastAPI

from app.router.user_router import router as user_router

app = FastAPI(title="stack-from-scratch-backend")


@app.get("/")
def root():
    return {"message": "API is running"}


app.include_router(user_router)