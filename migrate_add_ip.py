from app import app, db

def migrate_database():
    with app.app_context():
        # Add IP address column if it doesn't exist
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE pending_review ADD COLUMN ip_address VARCHAR(45)'))
                conn.commit()
            print("Successfully added ip_address column!")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("ip_address column already exists, skipping...")
            else:
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    migrate_database() 