import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.exception_handlers import (
    app_error_handler,
    sqlalchemy_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.api.routes.health import router as health_router
from app.api.routes.home import router as home_router
from app.api.routes.ipos import router as ipo_router
from app.exceptions import AppError


load_dotenv()

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]


app = FastAPI(
    title="Augur API",
    version="0.1.0",
    description="IPO data and allotment backend",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(
    RequestValidationError,
    validation_error_handler,
)
app.add_exception_handler(
    SQLAlchemyError,
    sqlalchemy_error_handler,
)
app.add_exception_handler(
    Exception,
    unhandled_error_handler,
)


app.include_router(health_router)
app.include_router(home_router)
app.include_router(ipo_router)