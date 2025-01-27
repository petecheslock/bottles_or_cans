from app.routes.main import bp as main_bp
from app.routes.admin import admin_bp
from app.routes.auth import auth_bp

__all__ = ['main_bp', 'admin_bp', 'auth_bp'] 