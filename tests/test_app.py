import unittest
import json
from datetime import datetime, timezone
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.review import Review, PendingReview
from app.models.rate_limit import RateLimit
from app.services.review import ReviewService
from app.services.rate_limit import RateLimitService
from app.config import TestingConfig

class FlaskAppTests(unittest.TestCase):
    def setUp(self):
        # Create test app with test config
        self.app = create_app(TestingConfig)
        self.app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test_secret_key',
            'WTF_CSRF_ENABLED': False
        })
        
        # Create test client with session handling
        self.client = self.app.test_client()
        with self.client.session_transaction() as sess:
            sess['_fresh'] = True  # Mark session as fresh
        
        # Create application context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create all tables in test database
        db.create_all()
        
        # Create test admin user
        admin = User(
            username='admin_test',
            is_admin=True
        )
        admin.set_password('test_password')
        db.session.add(admin)
        
        # Add some test reviews
        test_review = Review(
            text='Test review',
            votes_headphones=10,
            votes_wine=5
        )
        db.session.add(test_review)
        
        db.session.commit()

    def tearDown(self):
        # Clean up after each test
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Bottles or Cans?', response.data)
        self.assertIn(b'Welcome', response.data)

    def test_play_game_route(self):
        response = self.client.get('/play')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'bg-gray-50', response.data)
        self.assertIn(b'dark:bg-gray-900', response.data)
        self.assertIn(b'Bottles or Cans?', response.data)

    def test_admin_login(self):
        # Test invalid login
        response = self.client.post('/admin/login', data={
            'username': 'wrong_user',
            'password': 'wrong_password'
        }, follow_redirects=True)
        self.assertIn(b'Invalid credentials', response.data)

        # Test valid login
        response = self.client.post('/admin/login', 
            data={'username': 'admin_test', 'password': 'test_password'},
            follow_redirects=True)
        self.assertIn(b'Logged in successfully', response.data)

    def test_vote_functionality(self):
        review = Review.query.first()
        
        # Test headphones vote
        response = self.client.post('/vote', data={
            'review_id': review.id,
            'vote_type': 'headphones'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('headphones_percentage', data)
        self.assertIn('wine_percentage', data)

    def test_submit_review(self):
        # Test submitting review as non-admin
        response = self.client.post('/submit-review', data={
            'review_text': 'New test review',
            'captcha_answer': 'DUMMY'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Login as admin
        response = self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })
        
        # Set up the session properly
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = User.query.filter_by(username='admin_test').first().id

        # Test submitting review as admin
        response = self.client.post('/submit-review', data={
            'review_text': 'Admin test review'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Review added successfully', response.data)

    def test_manage_reviews(self):
        # First login as admin
        response = self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        }, follow_redirects=True)
        self.assertIn(b'Logged in successfully', response.data)

        # Then set up the session
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = User.query.filter_by(username='admin_test').first().id

        # Test viewing reviews
        response = self.client.get('/admin/manage-reviews')
        self.assertEqual(response.status_code, 200)

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Create a test rate limit
        rate_limit = RateLimit(
            ip_address='127.0.0.1',
            count=1,
            last_request=datetime.utcnow()
        )
        db.session.add(rate_limit)
        db.session.commit()

        # Test rate limit check
        result = RateLimitService.check_rate_limit('127.0.0.1')
        self.assertTrue(result)  # Should be under limit

        # Test exceeding rate limit
        rate_limit.count = 6  # Over default limit of 5
        db.session.commit()

        result = RateLimitService.check_rate_limit('127.0.0.1')
        self.assertFalse(result)  # Should be over limit

    def test_review_service(self):
        # Test creating review
        review = ReviewService.create_review('Test service review')
        self.assertIsNotNone(review.id)
        self.assertEqual(review.text, 'Test service review')
        
        # Test getting random review
        random_review = ReviewService.get_random_review()
        self.assertIsNotNone(random_review)
        
        # Test vote percentages
        headphones_pct, wine_pct = ReviewService.calculate_vote_percentages(review)
        self.assertIsInstance(headphones_pct, int)
        self.assertIsInstance(wine_pct, int)

    def test_pending_reviews(self):
        # Login as admin
        response = self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })
        
        # Set up the session properly
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = User.query.filter_by(username='admin_test').first().id

        # Create a pending review
        pending = PendingReview(text='Test pending review')
        db.session.add(pending)
        db.session.commit()

        # Test viewing pending reviews
        response = self.client.get('/admin/pending-reviews')
        self.assertEqual(response.status_code, 200)

    def test_review_actions(self):
        # Login as admin
        response = self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })
        
        # Set up the session properly
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user_id'] = User.query.filter_by(username='admin_test').first().id

        # Test approve action
        pending = PendingReview(text='Test pending review')
        db.session.add(pending)
        db.session.commit()
        
        response = self.client.post(
            f'/admin/approve-pending/{pending.id}',
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Review approved', response.data)

        # Test reject action
        pending = PendingReview(text='Test pending review 2')
        db.session.add(pending)
        db.session.commit()
        
        response = self.client.post(
            f'/admin/reject-pending/{pending.id}',
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Review rejected', response.data)

if __name__ == '__main__':
    unittest.main() 