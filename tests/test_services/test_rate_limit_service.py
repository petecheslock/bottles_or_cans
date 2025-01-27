from tests.base import BaseTestCase
from app.services.rate_limit import RateLimitService
from datetime import datetime

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