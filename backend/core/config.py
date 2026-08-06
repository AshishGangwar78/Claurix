import os

from backend.core.settings import get_settings

_settings = get_settings()
BASE_STORAGE_DIR = _settings.storage_dir or "backend/storage"

os.makedirs(BASE_STORAGE_DIR, exist_ok=True)
