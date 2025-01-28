from datetime import datetime, timezone, timedelta, UTC
from app.models.rate_limit import RateLimit
from app.extensions import db

class RateLimitService:
    @staticmethod
    def get_all_rate_limits():
        """Get all rate limit records"""
        return RateLimit.query.all()

    @staticmethod
    def create_rate_limit(ip_address):
        """Create a new rate limit record"""
        rate_limit = RateLimit(
            ip_address=ip_address,
            count=1,
            last_request=datetime.now(UTC)
        )
        db.session.add(rate_limit)
        db.session.commit()
        return rate_limit

    @staticmethod
    def check_rate_limit(ip_address, limit=5, window=3600):
        """Check if an IP has exceeded the rate limit"""
        # Clean up old entries first
        window_start = datetime.now(UTC) - timedelta(seconds=window)
        RateLimitService.cleanup_old_entries(window_start)
        
        rate_limit = db.session.execute(
            db.select(RateLimit).filter_by(ip_address=ip_address)
        ).scalar()
        
        if rate_limit:
            rate_limit.count += 1
            rate_limit.last_request = datetime.now(UTC)
            if rate_limit.count >= limit:
                rate_limit.is_blocked = True
                db.session.commit()
                return False
        else:
            rate_limit = RateLimitService.create_rate_limit(ip_address)
            
        db.session.commit()
        return True

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
    def cleanup_old_entries(cutoff=None):
        """Remove rate limit entries older than cutoff"""
        if cutoff is None:
            cutoff = datetime.now(UTC) - timedelta(seconds=3600)
        
        db.session.execute(
            db.delete(RateLimit).where(RateLimit.last_request < cutoff)
        )
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