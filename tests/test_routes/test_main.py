from tests.base import BaseTestCase
import json
from app.models.review import Review

class TestMainRoutes(BaseTestCase):
    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Bottles or Cans?', response.data)
        self.assertIn(b'Welcome', response.data)

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