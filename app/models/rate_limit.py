from app.extensions import db
from datetime import datetime

class RateLimit(db.Model):
    """Model for tracking rate limits."""
    __tablename__ = 'rate_limits'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), unique=True, nullable=False)
    count = db.Column(db.Integer, default=0)
    is_blocked = db.Column(db.Boolean, default=False)
    last_request = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<RateLimit {self.ip_address}>' 