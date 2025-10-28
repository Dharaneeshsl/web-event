import os
from decouple import config as env_config
from datetime import timedelta

class Config:
    # Flask Configuration
    SECRET_KEY = env_config('SECRET_KEY')  # No default - must be set
    DEBUG = env_config('DEBUG', default=False, cast=bool)
    TESTING = env_config('TESTING', default=False, cast=bool)
    
    # JWT Configuration
    JWT_SECRET_KEY = env_config('JWT_SECRET_KEY')  # No default - must be set
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=env_config('JWT_ACCESS_TOKEN_EXPIRES_HOURS', default=24, cast=int))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=env_config('JWT_REFRESH_TOKEN_EXPIRES_DAYS', default=30, cast=int))
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # Database Configuration
    MONGODB_URI = env_config('MONGODB_URI', default='mongodb://localhost:27017/hashquest')
    MONGODB_DATABASE = env_config('MONGODB_DATABASE', default='hashquest')
    
    
    # CORS Configuration
    CORS_ORIGINS = env_config('CORS_ORIGINS', default='http://localhost:3000,http://127.0.0.1:3000').split(',')
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With']
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    
    
    
    # Game Configuration
    MAX_TEAMS = env_config('MAX_TEAMS', default=20, cast=int)
    MAX_WORD_GUESSES = env_config('MAX_WORD_GUESSES', default=3, cast=int)
    GAME_WORD = env_config('GAME_WORD', default='POWERHOUSE')
    TOTAL_PAGES = env_config('TOTAL_PAGES', default=10, cast=int)
    
    # Security Configuration
    BCRYPT_LOG_ROUNDS = env_config('BCRYPT_LOG_ROUNDS', default=12, cast=int)
    PASSWORD_MIN_LENGTH = env_config('PASSWORD_MIN_LENGTH', default=6, cast=int)
    TEAM_CODE_LENGTH = env_config('TEAM_CODE_LENGTH', default=6, cast=int)
    ADMIN_TOKEN = env_config('ADMIN_TOKEN', default='admin-secret')
    
    # Logging Configuration
    LOG_LEVEL = env_config('LOG_LEVEL', default='INFO')
    LOG_FILE = env_config('LOG_FILE', default='logs/hashquest.log')
    
    # Monitoring
    SENTRY_DSN = env_config('SENTRY_DSN', default='')
    
    # WebSocket Configuration
    SOCKETIO_ASYNC_MODE = 'gevent'
    SOCKETIO_CORS_ALLOWED_ORIGINS = CORS_ORIGINS
    
    # API Configuration
    API_TITLE = 'HashQuest API'
    API_VERSION = 'v1'
    API_DESCRIPTION = 'API for HashQuest Web Event Game'
    API_DOC_URL = '/api/docs'
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = env_config('UPLOAD_FOLDER', default='uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv'}

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    MONGODB_URI = env_config('TEST_MONGODB_URI', default='mongodb://localhost:27017/hashquest_test')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'WARNING'

class StagingConfig(Config):
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'INFO'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = env_config('FLASK_ENV', default='development')
    return config.get(env, config['default'])