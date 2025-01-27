from tests.base import BaseTestCase

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