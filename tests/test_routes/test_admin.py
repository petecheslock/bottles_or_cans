from tests.base import BaseTestCase
from app.models.review import Review
from sqlalchemy import text

class TestAdminRoutes(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.login_admin()

    def test_manage_reviews(self):
        response = self.client.get('/admin/manage-reviews')
        self.assertEqual(response.status_code, 200)

    def test_pending_reviews(self):
        pending = self.create_pending_review('Test pending review')
        response = self.client.get('/admin/pending-reviews')
        self.assertEqual(response.status_code, 200)

    def test_review_actions(self):
        # Test approve action
        pending = self.create_pending_review('Test pending review')
        response = self.client.post(
            f'/admin/approve-pending/{pending.id}',
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Review approved', response.data)

        # Test reject action
        pending = self.create_pending_review('Test pending review 2')
        response = self.client.post(
            f'/admin/reject-pending/{pending.id}',
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Review rejected', response.data)

    def test_edit_review(self):
        review = self.create_test_review()
        
        # Test GET request
        response = self.client.get(f'/admin/edit-review/{review.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Edit Review', response.data)
        
        # Test POST request
        new_text = 'Updated review text'
        response = self.client.post(
            f'/admin/edit-review/{review.id}',
            data={'review_text': new_text},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Review updated successfully', response.data)
        
        # Verify the review was actually updated
        updated_review = self.db.session.get(Review, review.id)
        self.assertEqual(updated_review.text, new_text)

    def test_edit_review_with_vote_counts(self):
        """Test editing a review's text and vote counts"""
        review = self.create_test_review()
        initial_votes_headphones = review.votes_headphones
        initial_votes_wine = review.votes_wine
        
        # Test GET request shows current vote counts
        response = self.client.get(f'/admin/edit-review/{review.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(str(initial_votes_headphones).encode(), response.data)
        self.assertIn(str(initial_votes_wine).encode(), response.data)
        
        # Test POST request with updated vote counts
        new_text = 'Updated review text'
        new_votes_headphones = 42
        new_votes_wine = 58
        
        response = self.client.post(
            f'/admin/edit-review/{review.id}',
            data={
                'review_text': new_text,
                'votes_headphones': new_votes_headphones,
                'votes_wine': new_votes_wine
            },
            follow_redirects=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Review updated successfully', response.data)
        
        # Verify the review was actually updated
        updated_review = self.db.session.get(Review, review.id)
        self.assertEqual(updated_review.text, new_text)
        self.assertEqual(updated_review.votes_headphones, new_votes_headphones)
        self.assertEqual(updated_review.votes_wine, new_votes_wine)

    def test_edit_review_vote_counts_validation(self):
        """Test validation of vote count inputs"""
        review = self.create_test_review()
        initial_votes_headphones = review.votes_headphones
        initial_votes_wine = review.votes_wine
        
        # Test negative vote counts
        response = self.client.post(
            f'/admin/edit-review/{review.id}',
            data={
                'review_text': 'Test text',
                'votes_headphones': -5,
                'votes_wine': -10
            },
            follow_redirects=True
        )
        
        # Check for error message
        self.assertIn(b'Vote counts cannot be negative', response.data)
        
        # Verify votes were not updated
        updated_review = self.db.session.get(Review, review.id)
        self.assertEqual(updated_review.votes_headphones, initial_votes_headphones)
        self.assertEqual(updated_review.votes_wine, initial_votes_wine)

    def test_rate_limits_management(self):
        # Create some rate limits
        rate_limit = self.create_rate_limit('192.168.1.1', 1)
        
        # Test viewing rate limits
        response = self.client.get('/admin/rate-limits')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'192.168.1.1', response.data)
        
        # Test blocking IP
        response = self.client.post('/admin/rate-limits', data={
            'ip_address': '192.168.1.1',
            'action': 'block'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'IP address blocked successfully', response.data)
        
        # Test unblocking IP
        response = self.client.post('/admin/rate-limits', data={
            'ip_address': '192.168.1.1',
            'action': 'unblock'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'IP address unblocked successfully', response.data)

    def test_rate_limits_management_errors(self):
        """Test error handling in rate limits management"""
        # Test deleting non-existent rate limit
        response = self.client.post('/admin/rate-limits', data={
            'ip_address': '1.1.1.1',
            'action': 'delete'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rate limit record not found', response.data)
        
        # Test invalid action
        response = self.client.post('/admin/rate-limits', data={
            'ip_address': '1.1.1.1',
            'action': 'invalid'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_delete_review(self):
        """Test review deletion"""
        review = self.create_test_review()
        
        # Test successful deletion
        response = self.client.post(f'/admin/delete-review/{review.id}', 
                                  follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Review deleted successfully', response.data)
        
        # Verify review was deleted
        self.assertIsNone(self.db.session.get(Review, review.id))
        
        # Test deleting non-existent review
        response = self.client.post('/admin/delete-review/999', 
                                  follow_redirects=True)
        self.assertEqual(response.status_code, 404)

    def test_seed_reviews(self):
        """Test seeding reviews with random votes"""
        # Create some test reviews
        review1 = self.create_test_review()
        review2 = self.create_test_review()
        
        # Test AJAX request
        response = self.client.post('/admin/seed-reviews', 
                                  headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])
        
        # Test regular request
        response = self.client.post('/admin/seed-reviews', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Reviews seeded successfully', response.data)
        
        # Verify votes were updated
        updated_review1 = self.db.session.get(Review, review1.id)
        updated_review2 = self.db.session.get(Review, review2.id)
        self.assertGreaterEqual(updated_review1.votes_headphones, 0)
        self.assertLessEqual(updated_review1.votes_headphones, 100)
        self.assertGreaterEqual(updated_review1.votes_wine, 0)
        self.assertLessEqual(updated_review1.votes_wine, 100)

    def test_seed_reviews_ajax(self):
        """Test seeding reviews via AJAX request"""
        self.login_admin()
        
        # Create a test review
        review = self.create_test_review()
        initial_votes = review.votes_headphones
        
        # Test AJAX request
        response = self.client.post('/admin/seed-reviews', 
                                  headers={'X-Requested-With': 'XMLHttpRequest'})
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)  # Verify JSON response
        self.assertTrue(response.json['success'])
        
        # Verify votes were updated
        updated_review = self.db.session.get(Review, review.id)
        self.assertNotEqual(updated_review.votes_headphones, initial_votes) 

    def test_reset_all_votes_error(self):
        """Test error handling in reset all votes"""
        # Force an error by deleting the reviews table
        self.db.session.execute(text('DROP TABLE reviews'))
        self.db.session.commit()
        
        response = self.client.post('/admin/reset-all-votes')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json['success'])
        self.assertIn('message', response.json)