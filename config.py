import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or SECRET_KEY or 'change-me'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    UPLOAD_FOLDER = 'uploads'
    PERMANENT_SESSION_LIFETIME = 3600
    MAX_FILE_SIZE = 10 * 1024 * 1024
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_COOKIE_CSRF_PROTECT = False
    M365_CLIENT_ID = os.getenv('M365_CLIENT_ID')
    M365_CLIENT_SECRET = os.getenv('M365_CLIENT_SECRET')
    M365_TENANT_ID = os.getenv('M365_TENANT_ID')
    M365_REDIRECT_URI = os.getenv('M365_REDIRECT_URI')
    M365_SCOPES = ['openid', 'profile', 'email', 'offline_access']
    AZURE_SEARCH_ENDPOINT = os.getenv('AZURE_SEARCH_ENDPOINT') or os.getenv('VECTOR_STORE_ADDR')
    AZURE_SEARCH_KEY = os.getenv('AZURE_SEARCH_KEY') or os.getenv('VECTOR_STORE_KEY')
    AZURE_SEARCH_INDEX = os.getenv('AZURE_SEARCH_INDEX') or os.getenv('INDEX_NAME_DEV')
    AZURE_SEARCH_DEFAULT_TOP = int(os.getenv('AZURE_SEARCH_DEFAULT_TOP', 10))

class Development(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'

class Production(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')