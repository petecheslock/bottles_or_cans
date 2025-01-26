from flask import Flask, url_for, get_flashed_messages
from app.extensions import init_extensions, db
from app.config import DevelopmentConfig, TestingConfig, ProductionConfig
import os

def create_app(config_object=None):
    """Application factory function."""
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    # Configure the app
    if config_object is None:
        # Default configuration based on environment
        env = os.getenv('FLASK_ENV', 'development')
        if env == 'production':
            config_object = ProductionConfig
        elif env == 'testing':
            config_object = TestingConfig
        else:
            config_object = DevelopmentConfig
    
    app.config.from_object(config_object)
    
    # Set up logging
    if app.debug:
        app.logger.setLevel('DEBUG')
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Register template context processors
    register_template_processors(app)
    
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
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500 