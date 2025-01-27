import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-please-change')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Admin credentials - required for all environments
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
    
    def __init__(self):
        # Validate required settings
        if not self.ADMIN_USERNAME or not self.ADMIN_PASSWORD:
            raise ValueError(
                "ADMIN_USERNAME and ADMIN_PASSWORD must be set in environment "
                "or .env file!"
            )
    
    # Application settings
    CAPTCHA_LENGTH = int(os.getenv('CAPTCHA_LENGTH', 4))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///dev.db')

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///bottles_or_cans.db')
    
    def __init__(self):
        if not self.SECRET_KEY or self.SECRET_KEY == 'dev-key-please-change':
            raise ValueError("Production SECRET_KEY must be set!")
        if not self.ADMIN_PASSWORD:
            raise ValueError("Production ADMIN_PASSWORD must be set!")

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration class based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])