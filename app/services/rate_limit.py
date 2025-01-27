from datetime import datetime, timezone, timedelta
from app.models.rate_limit import RateLimit
from app.extensions import db

class RateLimitService:
    @staticmethod
    def get_all_rate_limits():
        """Get all rate limit records"""
        return RateLimit.query.all()

    @staticmethod
    def check_rate_limit(ip_address, limit=5, window=3600):
        """Check if an IP has exceeded the rate limit"""
        # Clean up old records
        RateLimitService._cleanup_old_records(window)
        
        # Get current count for IP
        rate_limit = RateLimit.query.filter_by(ip_address=ip_address).first()
        
        if not rate_limit:
            # Create new record if IP not found
            rate_limit = RateLimit(
                ip_address=ip_address, 
                count=1,
                last_request=datetime.utcnow()
            )
            db.session.add(rate_limit)
        else:
            # Update existing record
            if rate_limit.is_blocked:
                return False
            
            # Check if window has expired
            window_start = datetime.utcnow() - timedelta(seconds=window)
            if rate_limit.last_request < window_start:
                rate_limit.count = 1
            else:
                rate_limit.count += 1
            
            rate_limit.last_request = datetime.utcnow()
            
            # Check if limit exceeded
            if rate_limit.count > limit:
                rate_limit.is_blocked = True
            
        db.session.commit()
        return rate_limit.count <= limit

    @staticmethod
    def block_ip(ip_address):
        """Block an IP address"""
        rate_limit = RateLimit.query.filter_by(ip_address=ip_address).first()
        if not rate_limit:
            rate_limit = RateLimit(ip_address=ip_address, is_blocked=True)
            db.session.add(rate_limit)
        else:
            rate_limit.is_blocked = True
        db.session.commit()

    @staticmethod
    def unblock_ip(ip_address):
        """Unblock an IP address"""
        rate_limit = RateLimit.query.filter_by(ip_address=ip_address).first()
        if rate_limit:
            rate_limit.is_blocked = False
            rate_limit.count = 0
            db.session.commit()

    @staticmethod
    def _cleanup_old_records(window=3600):
        """Remove rate limit records older than the window"""
        cutoff = datetime.utcnow() - timedelta(seconds=window)
        RateLimit.query.filter(
            RateLimit.last_request < cutoff,
            RateLimit.is_blocked == False  # Keep blocked IPs
        ).delete()
        db.session.commit()

    @staticmethod
    def delete_rate_limit(ip_address):
        """Delete a rate limit record for an IP address"""
        rate_limit = RateLimit.query.filter_by(ip_address=ip_address).first()
        if rate_limit:
            db.session.delete(rate_limit)
            db.session.commit()
            return True
        return False 