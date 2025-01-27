from flask import Flask, url_for, get_flashed_messages, render_template
from app.extensions import init_extensions, db
from app.config import get_config
import os
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.main import bp as main_bp

def create_app(config_class=None):
    """Application factory function."""
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    # Load config
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)
    
    # Set up logging
    if app.debug:
        app.logger.setLevel('DEBUG')
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    
    # Register template context processors
    register_template_processors(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    @app.context_processor
    def utility_processor():
        return {
            'ga_measurement_id': app.config.get('GA_MEASUREMENT_ID')
        }
    
    return app

def register_blueprints(app):
    """Register Flask blueprints."""
    from app.routes import main_bp, admin_bp, auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)

def register_template_processors(app):
    """Register template context processors."""
    @app.context_processor
    def utility_processor():
        """Add utility functions to template context."""
        return dict(
            url_for=url_for,
            get_flashed_messages=get_flashed_messages
        )

def register_error_handlers(app):
    """Register error handlers."""
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500 