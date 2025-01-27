from app.models.user import User
from app.extensions import db
from werkzeug.security import check_password_hash, generate_password_hash

class UserService:
    @staticmethod
    def authenticate_admin(username, password):
        """Authenticate an admin user."""
        user = User.query.filter_by(username=username, is_admin=True).first()
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def change_admin_password(user_id, current_password, new_password, confirm_password):
        """Change admin user password"""
        user = db.session.get(User, user_id)
        if not user:
            return False, "User not found"
            
        # Verify current password
        if not user.check_password(current_password):
            return False, "Current password is incorrect"
            
        # Verify passwords match
        if new_password != confirm_password:
            return False, "Passwords do not match"
            
        # Update password
        user.set_password(new_password)
        db.session.commit()
        return True, "Password updated successfully"

    @staticmethod
    def create_admin(username, password):
        """Create a new admin user."""
        user = User(username=username, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_user_by_id(user_id):
        """Get a user by ID."""
        return db.session.get(User, user_id) 