from app import app, db, Review, PendingReview

def migrate_database():
    with app.app_context():
        # Create the PendingReview table without touching existing tables
        try:
            PendingReview.__table__.create(db.engine)
            print("Successfully created PendingReview table!")
        except Exception as e:
            if "already exists" in str(e):
                print("PendingReview table already exists, skipping...")
            else:
                print(f"Error creating table: {e}")

if __name__ == "__main__":
    migrate_database() 