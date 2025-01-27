from tests.base import BaseTestCase
from flask import url_for
from app.services.user import UserService
from app.models.user import User
from io import BytesIO

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

    def test_login_validation(self):
        """Test login form validation"""
        # Test missing username
        response = self.client.post('/admin/login', data={
            'password': 'test_password'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Username is required', response.data)

        # Test missing password
        response = self.client.post('/admin/login', data={
            'username': 'admin_test'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Password is required', response.data)

        # Test empty form submission
        response = self.client.post('/admin/login', data={}, 
                                  follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Username is required', response.data)

    def test_already_logged_in(self):
        """Test accessing login page when already logged in"""
        # First login
        self.login_admin()
        
        # Try accessing login page again
        response = self.client.get('/admin/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Should be redirected to dashboard with flash message
        self.assertIn(b'Dashboard', response.data)  # Verify we're on dashboard
        self.assertIn(b'You are already logged in', response.data)

    def test_logout_functionality(self):
        """Test complete logout functionality"""
        # First login
        self.login_admin()
        
        # Verify logged in state
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)
        
        # Test logout
        response = self.client.get('/admin/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged out successfully', response.data)
        
        # Verify session is cleared
        with self.client.session_transaction() as sess:
            self.assertNotIn('logged_in', sess)
            self.assertNotIn('user_id', sess)
        
        # Verify can't access protected routes after logout
        response = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Please log in', response.data)

    def test_change_password(self):
        """Test password change functionality"""
        # Login first
        self.login_admin()
        
        # Test successful password change
        response = self.client.post('/admin/users/change-password', data={
            'current_password': 'test_password',
            'new_password': 'new_password123',
            'confirm_password': 'new_password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Password updated successfully', response.data)
        
        # Test login with new password
        self.client.get('/admin/logout')
        response = self.client.post('/admin/login', data={
            'username': 'admin_test',
            'password': 'new_password123'
        }, follow_redirects=True)
        self.assertIn(b'Logged in successfully', response.data)

    def test_change_password_validation(self):
        """Test password change validation"""
        self.login_admin()
        
        # Test wrong current password
        response = self.client.post('/admin/users/change-password', data={
            'current_password': 'wrong_password',
            'new_password': 'new_pass',
            'confirm_password': 'new_pass'
        }, follow_redirects=True)
        self.assertIn(b'Current password is incorrect', response.data)
        
        # Test passwords don't match
        response = self.client.post('/admin/users/change-password', data={
            'current_password': 'test_password',
            'new_password': 'new_pass1',
            'confirm_password': 'new_pass2'
        }, follow_redirects=True)
        self.assertIn(b'Passwords do not match', response.data)

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

    def test_admin_index_redirect(self):
        """Test /admin and /admin/ redirect appropriately"""
        # Test both /admin and /admin/ when not logged in
        for route in ['/admin', '/admin/']:
            response = self.client.get(route, follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.location.endswith('/admin/login'))
        
        # Test both routes when logged in
        self.login_admin()
        for route in ['/admin', '/admin/']:
            response = self.client.get(route, follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.location.endswith('/admin/dashboard')) 