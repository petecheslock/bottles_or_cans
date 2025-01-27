from tests.base import BaseTestCase
from app.models.review import Review

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