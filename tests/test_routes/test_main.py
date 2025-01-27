from tests.base import BaseTestCase
import json
from app.models.review import Review
from flask import url_for

class TestMainRoutes(BaseTestCase):
    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Bottles or Cans?', response.data)

    def test_play_game_route(self):
        # Create a test review first
        self.create_test_review()
        
        response = self.client.get('/play')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'bg-gray-50', response.data)
        self.assertIn(b'dark:bg-gray-900', response.data)
        self.assertIn(b'Bottles or Cans?', response.data)

    def test_vote_functionality(self):
        review = self.create_test_review()
        
        response = self.client.post('/vote', data={
            'review_id': review.id,
            'vote_type': 'headphones'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('headphones_percentage', data)
        self.assertIn('wine_percentage', data)
        
        # If you need to verify the vote was recorded, use the new style:
        updated_review = self.db.session.get(Review, review.id)
        self.assertEqual(updated_review.votes_headphones, 11)  # 10 + 1

    def test_submit_review(self):
        # Test submitting review as non-admin
        response = self.client.post('/submit-review', data={
            'review_text': 'New test review',
            'captcha_answer': 'DUMMY'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) 

    def test_start_game(self):
        # Create a test review first
        self.create_test_review()
        
        response = self.client.get('/start', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertTrue(sess.get('seen_landing'))

    def test_submit_review_as_admin(self):
        # Login as admin first
        self.login_admin()
        
        response = self.client.post('/submit-review', data={
            'review_text': 'Admin review test'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Review added successfully', response.data)

    def test_submit_review_rate_limited(self):
        # Create rate limit
        self.create_rate_limit('127.0.0.1', 6)  # Over limit
        
        response = self.client.post('/submit-review', data={
            'review_text': 'Test review',
            'captcha_answer': 'DUMMY'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 429) 

    def test_vote_with_invalid_data(self):
        """Test voting with invalid data"""
        # Test invalid review_id
        response = self.client.post('/vote', data={
            'review_id': 999,
            'vote_type': 'headphones'
        })
        self.assertEqual(response.status_code, 404)

        # Test invalid vote_type
        review = self.create_test_review()
        response = self.client.post('/vote', data={
            'review_id': review.id,
            'vote_type': 'invalid'
        })
        self.assertEqual(response.status_code, 400)

    def test_submit_review_validation(self):
        """Test review submission validation"""
        # Test empty review text
        response = self.client.post('/submit-review', data={
            'review_text': '',
            'captcha_answer': 'DUMMY'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Review text is required', response.data)

        # Test too long review text
        response = self.client.post('/submit-review', data={
            'review_text': 'x' * 501,
            'captcha_answer': 'DUMMY'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Review text too long', response.data)

    def test_root_shows_landing_for_new_users(self):
        """Test that root URL shows landing page for new users"""
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to Bottles or Cans', response.data)

    def test_root_skips_landing_for_returning_users(self):
        """Test that root URL skips landing for users who've seen it"""
        with self.client.session_transaction() as sess:
            sess['seen_landing'] = True
        
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Bottles or Cans?', response.data) 