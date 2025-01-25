from app import app, db, User
from werkzeug.security import generate_password_hash
import getpass
import re
import argparse
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

def validate_username(username):
    if not 3 <= len(username) <= 20:
        return False, "Username must be between 3 and 20 characters"
    if not re.match("^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, ""

def get_admin_credentials():
    print("\n=== Create Admin User ===")
    
    while True:
        username = input("\nEnter admin username: ").strip()
        is_valid, message = validate_username(username)
        if is_valid:
            break
        print(f"Invalid username: {message}")
    
    while True:
        password = getpass.getpass("Enter admin password: ")
        is_valid, message = validate_password(password)
        if not is_valid:
            print(f"Invalid password: {message}")
            continue
            
        confirm_password = getpass.getpass("Confirm admin password: ")
        if password != confirm_password:
            print("Passwords do not match!")
            continue
            
        break
    
    return username, password

def migrate_database():
    with app.app_context():
        try:
            # Create users table
            print("\nChecking for users table...")
            User.__table__.create(db.engine)
            print("Successfully created users table!")
            
            # Check if any users exist
            if User.query.count() == 0:
                print("\nNo admin user found. Let's create one.")
                username, password = get_admin_credentials()
                
                default_admin = User(
                    username=username,
                    is_admin=True
                )
                default_admin.set_password(password)
                db.session.add(default_admin)
                db.session.commit()
                print("\nAdmin user created successfully!")
                print(f"Username: {username}")
                
            else:
                print("\nUsers already exist in the database.")
                
        except Exception as e:
            if "already exists" in str(e).lower():
                print("Users table already exists, skipping...")
            else:
                print(f"Error during migration: {e}")

def create_admin_user():
    print("Creating a new admin user...")
    username = input("Enter new admin username: ")
    password = input("Enter new admin password: ")

    new_admin = User(username=username, is_admin=True)
    new_admin.set_password(password)

    db.session.add(new_admin)
    db.session.commit()
    print("New admin user created successfully!")

def main():
    parser = argparse.ArgumentParser(description='Bottles or Cans - Admin User Setup')
    parser.add_argument('--force-new-admin', action='store_true', 
                       help='Create a new admin user even if users table exists')
    args = parser.parse_args()

    print("\nBottles or Cans - Admin User Setup")
    print("==================================\n")

    print("Debug: Parsed arguments:", vars(args))
    print("Debug: Force new admin flag:", args.force_new_admin)

    with app.app_context():
        inspector = inspect(db.engine)

        print("Checking for users table...")
        has_table = inspector.has_table("user")
        print("Debug: Has users table:", has_table)

        if has_table:
            print("Debug: Entering existing table logic")
            if args.force_new_admin:
                print("Debug: Force flag is True, creating new admin")
                create_admin_user()
            else:
                print("Debug: Force flag is False, skipping")
                print("Users table already exists")
                print("Use --force-new-admin flag to create a new admin user")
                print("Skipping...")
        else:
            print("Debug: Creating new table and admin")
            User.__table__.create(db.engine)
            print("Created users table")
            create_admin_user()

    print("\nSetup complete!")

if __name__ == "__main__":
    main() 