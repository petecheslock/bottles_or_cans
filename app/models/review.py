from datetime import datetime, timezone
from app.extensions import db

class Review(db.Model):
    """Model for storing reviews and their votes."""
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    votes_headphones = db.Column(db.Integer, default=0)
    votes_wine = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

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
        return f'<Review {self.id}>'

class PendingReview(db.Model):
    """Model for storing reviews pending admin approval."""
    __tablename__ = 'pending_review'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    status = db.Column(db.String(20), default='pending')

    def __repr__(self):
        return f'<PendingReview {self.id}>' 