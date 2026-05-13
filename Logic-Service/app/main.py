from fastapi import FastAPI

from app.routers import logic

app = FastAPI(title="Logic Service")

app.include_router(logic.router)
