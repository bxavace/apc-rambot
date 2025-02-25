import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'None'
    UPLOAD_FOLDER = 'uploads'
    PERMANENT_SESSION_LIFETIME = 3600

class Development(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'

class Production(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')