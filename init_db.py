import json
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.review import Review, PendingReview
import getpass

def create_tables():
    """Create all necessary tables in the database."""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Database and tables created successfully!")

def import_reviews_from_json():
    """Import reviews from reviews_export.json if it exists."""
    app = create_app()
    try:
        with open('reviews_export.json', 'r') as f:
            reviews = json.load(f)
        
        with app.app_context():
            # Check if reviews table is empty
            if Review.query.count() == 0:
                for review_data in reviews:
                    new_review = Review(
                        id=review_data['id'],
                        text=review_data['text'],
                        votes_headphones=review_data['votes_headphones'],
                        votes_wine=review_data['votes_wine'],
                        created_at=datetime.strptime(review_data['created_at'], '%Y-%m-%d %H:%M:%S.%f')
                    )
                    db.session.add(new_review)
                db.session.commit()
                print(f"Imported {len(reviews)} reviews from backup")
            else:
                print("Reviews table not empty, skipping import")
                
    except FileNotFoundError:
        print("No reviews backup found (reviews_export.json)")
    except Exception as e:
        print(f"Error importing reviews: {e}")
        db.session.rollback()

def create_admin_user():
    """Prompt for admin user credentials and create the user."""
    app = create_app()
    print("\n=== Create Admin User ===")
    
    while True:
        username = input("\nEnter admin username: ").strip()
        if not (3 <= len(username) <= 20) or not username.isalnum():
            print("Invalid username: must be 3-20 characters and alphanumeric.")
            continue
        break
    
    while True:
        password = getpass.getpass("Enter admin password: ")
        if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.islower() for c in password) or not any(c.isdigit() for c in password):
            print("Invalid password: must be at least 8 characters long, contain upper and lower case letters, and at least one number.")
            continue
            
        confirm_password = getpass.getpass("Confirm admin password: ")
        if password != confirm_password:
            print("Passwords do not match!")
            continue
            
        break
    
    with app.app_context():
        if not User.query.filter_by(username=username).first():
            new_admin = User(username=username, is_admin=True)
            new_admin.set_password(password)
            db.session.add(new_admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print(f"User '{username}' already exists!")

def main():
    """Main function to initialize the database."""
    create_tables()
    import_reviews_from_json()
    
    app = create_app()
    with app.app_context():
        if User.query.count() == 0:  # Check if there are no users
            create_admin_user()
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    main()
    print("Database initialized successfully!") 