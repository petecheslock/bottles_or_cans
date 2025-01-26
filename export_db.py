import sqlite3
import json
from datetime import datetime

def datetime_handler(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def export_reviews():
    # Connect to the database
    conn = sqlite3.connect('instance/bottles_or_cans.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all reviews
    cursor.execute('SELECT * FROM review')
    reviews = [dict(row) for row in cursor.fetchall()]

    # Export to JSON file
    with open('reviews_export.json', 'w') as f:
        json.dump(reviews, f, indent=2, default=datetime_handler)

    print(f"Exported {len(reviews)} reviews to reviews_export.json")
    conn.close()

if __name__ == '__main__':
    export_reviews() 