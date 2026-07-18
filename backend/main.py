from fastapi import FastAPI

from backend.api.routes import router
from backend.core import config as _config  # noqa: F401  # ensures storage dir exists

app = FastAPI()

app.include_router(router)
