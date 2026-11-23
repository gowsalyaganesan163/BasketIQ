
import os


class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get("SECRET_KEY", "basketiq-dev-key")
    DEBUG = True

    # File upload configuration
    UPLOAD_FOLDER = "data/processed"
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {"csv", "xlsx"}

    # Association mining defaults
    DEFAULT_MIN_SUPPORT = 0.02
    DEFAULT_MIN_CONFIDENCE = 0.30
    DEFAULT_MIN_LIFT = 1.0

    # Temporal analysis defaults
    LIFT_CHANGE_THRESHOLD = 0.10
