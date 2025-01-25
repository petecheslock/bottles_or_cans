import os
import pandas as pd
from app import app, db, User, Review, PendingReview

def create_tables():
    """Create all necessary tables in the database."""
    with app.app_context():
        db.create_all()
        print("Database and tables created successfully!")

def import_reviews_from_csv():
    """Import reviews from reviews.csv if it exists."""
    csv_file = 'reviews.csv'
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file)
            print(f"Debug: Found {len(df)} rows in {csv_file}.")
            with app.app_context():
                for index, row in df.iterrows():
                    print(f"Debug: Importing review {index + 1}: {row['text']}, Votes Headphones: {row.get('votes_headphones', 0)}, Votes Wine: {row.get('votes_wine', 0)}")
                    
                    new_review = Review(
                        text=row['text'],
                        votes_headphones=row.get('votes_headphones', 0),
                        votes_wine=row.get('votes_wine', 0)
                    )
                    db.session.add(new_review)
                db.session.commit()
                print(f"Imported {len(df)} reviews from {csv_file}.")
        except Exception as e:
            print(f"Error importing reviews: {e}")
            db.session.rollback()
    else:
        print(f"{csv_file} not found. No reviews imported.")

def create_admin_user():
    """Prompt for admin user credentials and create the user."""
    print("\n=== Create Admin User ===")
    
    while True:
        username = input("\nEnter admin username: ").strip()
        if not (3 <= len(username) <= 20) or not username.isalnum():
            print("Invalid username: must be 3-20 characters and alphanumeric.")
            continue
        break
    
    while True:
        password = input("Enter admin password: ")
        if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.islower() for c in password) or not any(c.isdigit() for c in password):
            print("Invalid password: must be at least 8 characters long, contain upper and lower case letters, and at least one number.")
            continue
            
        confirm_password = input("Confirm admin password: ")
        if password != confirm_password:
            print("Passwords do not match!")
            continue
            
        break
    
    new_admin = User(username=username, is_admin=True)
    new_admin.set_password(password)
    
    with app.app_context():
        db.session.add(new_admin)
        db.session.commit()
        print("Admin user created successfully!")

def main():
    """Main function to initialize the database."""
    create_tables()
    import_reviews_from_csv()
    
    with app.app_context():
        if User.query.count() == 0:  # Check if there are no users
            create_admin_user()
        else:
            print("Admin user already exists.")

if __name__ == "__main__":
    main() 