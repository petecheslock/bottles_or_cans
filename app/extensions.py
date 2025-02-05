from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask import current_app
import sys

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def init_admin_user(app):
    """Initialize admin user and import initial data if needed"""
    # Skip admin creation if configured (for testing)
    if app.config.get('SKIP_ADMIN_CREATION'):
        return
        
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check for admin user
        from app.models.user import User
        admin = User.query.filter_by(username=app.config['ADMIN_USERNAME']).first()
        
        if not admin:
            # Check if we have admin credentials configured
            if not app.config['ADMIN_USERNAME'] or not app.config['ADMIN_PASSWORD']:
                app.logger.error("""
                    No admin user found and admin credentials not configured!
                    Please set ADMIN_USERNAME and ADMIN_PASSWORD in your environment 
                    or .env file.
                """)
                sys.exit(1)
            
            # Create admin user
            try:
                admin = User(
                    username=app.config['ADMIN_USERNAME'],
                    is_admin=True
                )
                admin.set_password(app.config['ADMIN_PASSWORD'])
                db.session.add(admin)
                db.session.commit()
                app.logger.info(f"Created admin user: {app.config['ADMIN_USERNAME']}")
                
                # After creating admin, check for initial data file
                import os
                import json
                from app.services.user import UserService
                
                reviews_file = os.path.join(app.root_path, '..', 'reviews_export.json')
                if os.path.exists(reviews_file):
                    try:
                        with open(reviews_file, 'r') as f:
                            data = json.load(f)
                            UserService.import_initial_data(data)
                            app.logger.info("Imported initial reviews from reviews_export.json")
                    except Exception as e:
                        app.logger.error(f"Failed to import initial reviews: {str(e)}")
                
            except Exception as e:
                app.logger.error(f"Failed to create admin user: {str(e)}")
                sys.exit(1)


def init_extensions(app):
    """Initialize Flask extensions."""
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Configure login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Initialize admin user
    init_admin_user(app) 