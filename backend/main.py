from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.core import config as _config  # noqa: F401  # ensures storage dir exists
from backend.core.logging import configure_logging
from backend.copilot.routers.copilot_router import router as copilot_router

configure_logging()

app = FastAPI(title="Insurance Gap Analysis")

# Allow local frontend apps to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(copilot_router)
