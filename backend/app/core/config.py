import os

class Config:

    SECRET_KEY = "dxcon-secret"

    JWT_SECRET_KEY = "dxcon-jwt"

    SQLALCHEMY_DATABASE_URI = "sqlite:///dxcon.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
