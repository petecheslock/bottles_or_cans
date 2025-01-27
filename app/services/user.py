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

    @staticmethod
    def get_admin_user():
        """Check if admin user exists"""
        return User.query.filter_by(is_admin=True).first()

    @staticmethod
    def create_admin_user(username, password):
        """Create the admin user"""
        admin = User(
            username=username,
            is_admin=True
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        return admin

    @staticmethod
    def import_initial_data(data):
        """Import initial data from JSON"""
        try:
            # Handle reviews import
            from app.models.review import Review
            from datetime import datetime
            
            print(f"Importing data: {data}")  # Debug print
            
            # If data is a list, it's the reviews export format
            if isinstance(data, list):
                for review_data in data:
                    review = Review(
                        id=review_data.get('id'),
                        text=review_data['text'],
                        votes_headphones=review_data.get('votes_headphones', 0),
                        votes_wine=review_data.get('votes_wine', 0),
                        created_at=datetime.strptime(
                            review_data['created_at'], 
                            '%Y-%m-%d %H:%M:%S.%f'
                        ) if review_data.get('created_at') else datetime.utcnow()
                    )
                    db.session.add(review)
                    print(f"Added review: {review.text}")  # Debug print
            
            # If data is a dict, it's the legacy format with users and reviews
            elif isinstance(data, dict):
                if 'users' in data:
                    for user_data in data['users']:
                        if not User.query.filter_by(username=user_data['username']).first():
                            user = User(
                                username=user_data['username'],
                                is_admin=user_data.get('is_admin', False)
                            )
                            user.set_password(user_data['password'])
                            db.session.add(user)
                
                if 'reviews' in data:
                    for review_data in data['reviews']:
                        review = Review(
                            text=review_data.get('content', ''),  # Handle legacy 'content' field
                            votes_headphones=review_data.get('votes_headphones', 0),
                            votes_wine=review_data.get('votes_wine', 0)
                        )
                        db.session.add(review)
            
            db.session.commit()
            print("Commit successful")  # Debug print
        except Exception as e:
            print(f"Error during import: {str(e)}")  # Debug print
            db.session.rollback()
            raise e 