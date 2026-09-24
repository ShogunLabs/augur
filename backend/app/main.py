from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.ipos import router as ipo_router


app = FastAPI(
    title="Augur API",
    version="0.1.0",
    description="IPO data and allotment backend",
)

app.include_router(health_router)
app.include_router(ipo_router)