from app.models.user import User
from app.extensions import db

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
        """Change an admin's password."""
        user = User.query.filter_by(id=user_id, is_admin=True).first()
        if not user:
            return False
            
        if not user.check_password(current_password):
            return False
            
        if new_password != confirm_password:
            return False
            
        user.set_password(new_password)
        db.session.commit()
        return True

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
        return User.query.get(user_id) 