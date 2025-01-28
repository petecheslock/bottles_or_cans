from datetime import datetime, timezone, UTC
from app.extensions import db
from sqlalchemy.sql import func

class Review(db.Model):
    """Model for storing reviews and their votes."""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    votes_headphones = db.Column(db.Integer, default=0)
    votes_wine = db.Column(db.Integer, default=0)
    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    is_active = db.Column(db.Boolean, default=True)

    @property
    def total_votes(self):
        """Calculate total number of votes."""
        return self.votes_headphones + self.votes_wine

    @property
    def headphones_percentage(self):
        """Calculate percentage of headphone votes."""
        if self.total_votes == 0:
            return 0
        return round((self.votes_headphones / self.total_votes) * 100, 2)

    @property
    def wine_percentage(self):
        """Calculate percentage of wine votes."""
        if self.total_votes == 0:
            return 0
        return round((self.votes_wine / self.total_votes) * 100, 2)

    def __repr__(self):
        return f'<Review {self.text[:30]}...>'

    def increment_votes(self, vote_type):
        """Increment votes for the specified type"""
        if vote_type == 'headphones':
            self.votes_headphones += 1
        elif vote_type == 'wine':
            self.votes_wine += 1
            
    def reset_votes(self):
        """Reset all votes to zero"""
        self.votes_headphones = 0
        self.votes_wine = 0

class PendingReview(db.Model):
    """Model for storing reviews pending admin approval."""
    __tablename__ = 'pending_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    status = db.Column(db.String(20), default='pending')

    def __repr__(self):
        return f'<PendingReview {self.text[:30]}...>'

    def approve(self):
        """Convert pending review to active review"""
        review = Review(text=self.text, is_active=True)
        db.session.add(review)
        return review 