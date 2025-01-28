import unittest
from datetime import datetime, UTC
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.review import Review, PendingReview
from app.models.rate_limit import RateLimit
from app.config import TestingConfig

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.db = db
        
        # Drop and recreate all tables
        db.drop_all()
        db.create_all()
        
        # Create test admin user
        self.admin = User.query.filter_by(username='admin_test').first()
        if not self.admin:
            self.admin = User(username='admin_test', is_admin=True)
            self.admin.set_password('test_password')
            db.session.add(self.admin)
            db.session.commit()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.app_context.pop()

    def create_admin_user(self, username='new_admin_test'):
        """Create a new admin user with a unique username"""
        admin = User(username=username, is_admin=True)
        admin.set_password('test_password')
        self.db.session.add(admin)
        self.db.session.commit()
        return admin

    def create_test_review(self, text='Test review'):
        review = Review(
            text=text,
            votes_headphones=10,
            votes_wine=5
        )
        self.db.session.add(review)
        self.db.session.commit()
        
        # Refresh the review object to ensure we have the latest data
        return self.db.session.get(Review, review.id)

    def create_pending_review(self, text='Test pending review'):
        pending = PendingReview(text=text)
        self.db.session.add(pending)
        self.db.session.commit()
        return pending

    def create_rate_limit(self, ip_address, count):
        rate_limit = RateLimit(
            ip_address=ip_address,
            count=count,
            last_request=datetime.now(UTC)
        )
        self.db.session.add(rate_limit)
        self.db.session.commit()
        return rate_limit

    def login_admin(self):
        self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = self.admin.id 