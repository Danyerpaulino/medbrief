from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.briefings import router as briefings_router

app = FastAPI(title="MedBrief API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(briefings_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
