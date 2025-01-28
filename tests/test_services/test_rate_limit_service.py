from tests.base import BaseTestCase
from app.services.rate_limit import RateLimitService
from datetime import datetime, timedelta, UTC
from sqlalchemy import select
from app.models.rate_limit import RateLimit
from app.extensions import db

class TestRateLimitService(BaseTestCase):
    def test_rate_limiting(self):
        # Create a test rate limit
        rate_limit = self.create_rate_limit('127.0.0.1', 1)

        # Test rate limit check
        result = RateLimitService.check_rate_limit('127.0.0.1')
        self.assertTrue(result)  # Should be under limit

        # Test exceeding rate limit
        rate_limit.count = 6  # Over default limit of 5
        self.db.session.commit()

        result = RateLimitService.check_rate_limit('127.0.0.1')
        self.assertFalse(result)  # Should be over limit

    def test_cleanup_old_records(self):
        # Create some old rate limits
        old_rate_limit = self.create_rate_limit('10.0.0.1', 1)
        old_rate_limit.last_request = datetime.now(UTC) - timedelta(hours=2)
        old_rate_limit_id = old_rate_limit.id
        self.db.session.commit()
        
        # Create some recent rate limits
        recent_rate_limit = self.create_rate_limit('10.0.0.2', 1)
        recent_rate_limit_id = recent_rate_limit.id
        self.db.session.commit()
        
        RateLimitService.cleanup_old_entries()
        
        # Clear the session entirely to ensure fresh data
        self.db.session.close()
        
        # Check that old records were cleaned up using fresh queries
        old_record = self.db.session.execute(
            select(RateLimit).where(RateLimit.id == old_rate_limit_id)
        ).scalar()
        self.assertIsNone(old_record)
        
        # Check that recent records remain
        recent_record = self.db.session.execute(
            select(RateLimit).where(RateLimit.id == recent_rate_limit_id)
        ).scalar()
        self.assertIsNotNone(recent_record)

    def test_block_unblock_ip(self):
        # Test blocking IP
        RateLimitService.block_ip('10.0.0.3')
        rate_limit = self.db.session.execute(
            select(RateLimit).filter_by(ip_address='10.0.0.3')
        ).scalar_one()
        self.assertTrue(rate_limit.is_blocked)
        
        # Test unblocking IP
        RateLimitService.unblock_ip('10.0.0.3')
        rate_limit = self.db.session.execute(
            select(RateLimit).filter_by(ip_address='10.0.0.3')
        ).scalar_one()
        self.assertFalse(rate_limit.is_blocked) 