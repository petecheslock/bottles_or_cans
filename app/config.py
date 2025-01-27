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
    
    # Application settings
    CAPTCHA_LENGTH = int(os.getenv('CAPTCHA_LENGTH', 4))
    MAX_REVIEW_LENGTH = int(os.getenv('MAX_REVIEW_LENGTH', 500))
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        if not cls.ADMIN_USERNAME or not cls.ADMIN_PASSWORD:
            raise ValueError(
                "ADMIN_USERNAME and ADMIN_PASSWORD must be set in environment "
                "or .env file!"
            )

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
    
    @classmethod
    def validate_config(cls):
        """Additional validation for production"""
        super().validate_config()
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-key-please-change':
            raise ValueError("Production SECRET_KEY must be set!")

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration class based on environment."""
    # Check both FLASK_ENV and FLASK_DEBUG to determine environment
    env = os.getenv('FLASK_ENV')
    debug = os.getenv('FLASK_DEBUG')
    
    # If FLASK_DEBUG is '0' or FLASK_ENV is 'production', use production config
    if debug == '0' or env == 'production':
        environment = 'production'
    else:
        environment = 'development'
    
    config_class = config.get(environment, config['default'])
    config_class.validate_config()
    return config_class