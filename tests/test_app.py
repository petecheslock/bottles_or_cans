import unittest
import os
from app import app, db, User, Review, PendingReview, RateLimit
from datetime import datetime, timezone
import json
from base64 import b64decode

class FlaskAppTests(unittest.TestCase):
    def setUp(self):
        # Configure app for testing with in-memory database
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Change to in-memory database
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'test_secret_key'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.client = app.test_client()
        
        # Create all tables in test database
        with app.app_context():
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
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Check for content we know should be in the landing page
        self.assertIn(b'Bottles or Cans?', response.data)
        self.assertIn(b'Welcome', response.data)

    def test_play_game_route(self):
        response = self.client.get('/play')
        self.assertEqual(response.status_code, 200)
        # Check for Tailwind classes and content we know should be in the game page
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
        response = self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        }, follow_redirects=True)
        self.assertIn(b'Logged in successfully', response.data)

    def test_vote_functionality(self):
        with app.app_context():
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
        # Test submitting review as non-admin (should create pending review)
        response = self.client.post('/submit-review', data={
            'review_text': 'New test review',
            'captcha_answer': 'DUMMY'  # You might need to mock the captcha
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Login as admin
        self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })

        # Test submitting review as admin (should create direct review)
        response = self.client.post('/submit-review', data={
            'review_text': 'Admin test review'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Review added successfully', response.data)

    def test_manage_reviews(self):
        # Login as admin first
        self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })

        # Test viewing reviews
        response = self.client.get('/admin/manage-reviews')
        self.assertEqual(response.status_code, 200)

        # Test editing review - Update URL here
        with app.app_context():
            review = Review.query.first()
            response = self.client.post(f'/admin/edit-review/{review.id}', data={  # Changed from '/edit-review'
                'review_text': 'Updated review text'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Review updated successfully', response.data)

    def test_rate_limiting(self):
        with app.app_context():
            # Create initial rate limit record with 4 attempts
            rate_limit = RateLimit(
                ip_address='127.0.0.1',
                attempt_count=4,  # Start with 4 attempts
                last_attempt=datetime.now(timezone.utc)
            )
            db.session.add(rate_limit)
            db.session.commit()

            # Test that we're not rate limited yet at 4 attempts
            self.assertFalse(rate_limit.is_rate_limited())
            self.assertFalse(rate_limit.is_blocked)

            # Simulate another attempt (bringing total to 5)
            rate_limit.attempt_count += 1
            db.session.commit()

            # Should now be rate limited at 5 attempts
            self.assertTrue(rate_limit.is_rate_limited())
            self.assertFalse(rate_limit.is_blocked)  # Not blocked yet

            # Simulate one more attempt (bringing total to 6)
            rate_limit.attempt_count += 1
            rate_limit.is_blocked = True  # This gets set in check_rate_limit
            db.session.commit()

            # Should now be both rate limited and blocked
            self.assertTrue(rate_limit.is_rate_limited())
            self.assertTrue(rate_limit.is_blocked)

            # Test resetting after time window
            old_time = datetime.now(timezone.utc).replace(year=2020)
            rate_limit.last_attempt = old_time
            db.session.commit()
            self.assertFalse(rate_limit.is_rate_limited())  # Should not be rate limited due to old timestamp

    def test_captcha_refresh(self):
        response = self.client.post('/refresh-captcha')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('captcha_image', data)
        # Verify the captcha_image is valid base64
        try:
            b64decode(data['captcha_image'])
        except Exception:
            self.fail("Captcha image is not valid base64")

    def test_admin_dashboard(self):
        # Test access without login
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 302)  # Should redirect to login

        # Login and test access
        self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)

    def test_admin_logout(self):
        # Login first
        self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })
        
        # Test logout
        response = self.client.get('/admin/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged out successfully', response.data)

    def test_delete_review(self):
        # Login as admin
        self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })

        with app.app_context():
            review = Review.query.first()
            # Update URL
            response = self.client.post(f'/admin/delete-review/{review.id}', follow_redirects=True)  # Changed from '/delete-review'
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Review deleted successfully', response.data)

    def test_reset_votes(self):
        # Login as admin
        self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })

        # Test successful reset
        response = self.client.post('/reset-votes')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

        # Verify votes were reset
        with app.app_context():
            review = Review.query.first()
            self.assertEqual(review.votes_headphones, 0)
            self.assertEqual(review.votes_wine, 0)

    def test_pending_reviews(self):
        # Login as admin
        self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })

        # Create a pending review
        with app.app_context():
            pending = PendingReview(text='Test pending review')
            db.session.add(pending)
            db.session.commit()

        # Test viewing pending reviews - Update URL
        response = self.client.get('/admin/pending-reviews')  # Changed from '/pending-reviews'
        self.assertEqual(response.status_code, 200)

    def test_review_actions(self):
        # Login as admin
        self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })

        # Create a pending review
        with app.app_context():
            pending = PendingReview(text='Test pending review')
            db.session.add(pending)
            db.session.commit()
            review_id = pending.id

        # Test approve action
        response = self.client.post(f'/review-action/{review_id}/approve', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Review approved', response.data)

        # Create another pending review for reject test
        with app.app_context():
            pending = PendingReview(text='Test pending review 2')
            db.session.add(pending)
            db.session.commit()
            review_id = pending.id

        # Test reject action
        response = self.client.post(f'/review-action/{review_id}/reject', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Review rejected', response.data)

    def test_manage_rate_limits(self):
        # Login as admin
        self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })

        # Create a rate limit record
        with app.app_context():
            rate_limit = RateLimit(ip_address='127.0.0.1')
            db.session.add(rate_limit)
            db.session.commit()

        # Test viewing rate limits
        response = self.client.get('/admin/rate-limits')
        self.assertEqual(response.status_code, 200)

        # Test unblocking IP
        response = self.client.post('/admin/rate-limits', data={
            'ip_address': '127.0.0.1',
            'action': 'unblock'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'IP address unblocked successfully', response.data)

        # Test blocking IP
        response = self.client.post('/admin/rate-limits', data={
            'ip_address': '127.0.0.1',
            'action': 'block'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'IP address blocked successfully', response.data)

        # Test deleting rate limit record
        response = self.client.post('/admin/rate-limits', data={
            'ip_address': '127.0.0.1',
            'action': 'delete'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rate limit record deleted successfully', response.data)

    def test_manage_users(self):
        # Login as admin
        self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'test_password'
        })

        # Test viewing users
        response = self.client.get('/admin/users')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'admin_test', response.data)

    def test_rate_limit_is_rate_limited(self):
        with app.app_context():
            # Create a rate limit with multiple attempts
            rate_limit = RateLimit(
                ip_address='127.0.0.1',
                last_attempt=datetime.now(timezone.utc),  # Use UTC time
                attempt_count=6  # Exceed the default limit of 5
            )
            db.session.add(rate_limit)
            db.session.commit()
            
            # Test rate limiting
            self.assertTrue(rate_limit.is_rate_limited())

            # Test after resetting attempts
            rate_limit.attempt_count = 1
            db.session.commit()
            self.assertFalse(rate_limit.is_rate_limited())

            # Test with old timestamp (should not be rate limited)
            old_time = datetime.now(timezone.utc).replace(year=2020)
            rate_limit.last_attempt = old_time
            rate_limit.attempt_count = 6
            db.session.commit()
            self.assertFalse(rate_limit.is_rate_limited())

if __name__ == '__main__':
    unittest.main() 