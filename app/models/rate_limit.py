from datetime import datetime, timezone
from app.extensions import db

class RateLimit(db.Model):
    """Model for tracking rate limits."""
    __tablename__ = 'rate_limit'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    endpoint = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False)
    attempt_count = db.Column(db.Integer, default=1)
    is_blocked = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<RateLimit {self.ip_address}:{self.endpoint}>' 