from tests.base import BaseTestCase

class TestAuthRoutes(BaseTestCase):
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

    def test_login_required_redirect(self):
        """Test login required redirects"""
        # Logout first
        self.client.get('/admin/logout')
        
        # Try accessing protected routes
        protected_routes = [
            '/admin/dashboard',
            '/admin/manage-reviews',
            '/admin/pending-reviews',
            '/admin/rate-limits'
        ]
        
        for route in protected_routes:
            response = self.client.get(route, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Please log in', response.data)
            self.assertIn(b'Login', response.data)

    def test_session_handling(self):
        """Test session handling"""
        # Test session after login
        self.login_admin()
        with self.client.session_transaction() as sess:
            self.assertTrue(sess.get('logged_in'))
            self.assertIsNotNone(sess.get('user_id'))
        
        # Test session after logout
        self.client.get('/admin/logout')
        with self.client.session_transaction() as sess:
            self.assertFalse(sess.get('logged_in', False))
            self.assertIsNone(sess.get('user_id')) 