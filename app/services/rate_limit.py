from datetime import datetime, timezone
from app.models.rate_limit import RateLimit
from app.extensions import db

class RateLimitService:
    @staticmethod
    def check_rate_limit(ip_address, endpoint, limit_minutes=30, max_attempts=5):
        """Check if an IP address is rate limited."""
        rate_limit = RateLimit.query.filter_by(
            ip_address=ip_address,
            endpoint=endpoint
        ).first()

        current_time = datetime.now(timezone.utc)
        
        if not rate_limit:
            rate_limit = RateLimit(
                ip_address=ip_address,
                endpoint=endpoint,
                timestamp=current_time
            )
            db.session.add(rate_limit)
            db.session.commit()
            return True

        # Ensure timestamp is timezone-aware
        if rate_limit.timestamp.tzinfo is None:
            rate_limit.timestamp = rate_limit.timestamp.replace(tzinfo=timezone.utc)
            
        time_diff = current_time - rate_limit.timestamp
        
        # Reset if outside time window
        if time_diff.total_seconds() >= (limit_minutes * 60):
            rate_limit.timestamp = current_time
            rate_limit.attempt_count = 1
            db.session.commit()
            return True
            
        # Check if too many attempts
        if rate_limit.attempt_count >= max_attempts:
            return False
            
        rate_limit.attempt_count += 1
        rate_limit.timestamp = current_time
        db.session.commit()
        return True

    @staticmethod
    def block_ip(ip_address):
        """Block an IP address."""
        rate_limit = RateLimit.query.filter_by(ip_address=ip_address).first()
        if rate_limit:
            rate_limit.is_blocked = True
            db.session.commit()
        return rate_limit

    @staticmethod
    def unblock_ip(ip_address):
        """Unblock an IP address."""
        rate_limit = RateLimit.query.filter_by(ip_address=ip_address).first()
        if rate_limit:
            rate_limit.is_blocked = False
            rate_limit.attempt_count = 0
            db.session.commit()
        return rate_limit 