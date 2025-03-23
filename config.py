import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    UPLOAD_FOLDER = 'uploads'
    PERMANENT_SESSION_LIFETIME = 3600
    SESSION_PERMANENT = True
    SESSION_TYPE = 'filesystem'
    MAX_FILE_SIZE = 10 * 1024 * 1024

class Development(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'

class Production(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')