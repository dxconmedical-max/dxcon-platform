import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dxcon-dev-secret"
    )

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "dxcon-dev-jwt"
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///dxcon.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_ENV = os.getenv(
        "APP_ENV",
        "development"
    )

    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )

    LOG_FORMAT = os.getenv(
        "LOG_FORMAT",
        "text"
    )

    REQUEST_ID_HEADER = os.getenv(
        "REQUEST_ID_HEADER",
        "X-Request-ID"
    )
