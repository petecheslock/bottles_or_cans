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

    def test_setup_page_accessible_when_no_admin(self):
        """Test that setup page is accessible when no admin exists"""
        # First ensure no admin exists by clearing all users
        self.db.session.close()
        self.db.session.query(User).delete()
        self.db.session.commit()
        
        # Now try accessing the setup page
        response = self.client.get('/admin/setup')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'First-Time Setup', response.data)

    def test_setup_page_redirects_when_admin_exists(self):
        """Test that setup page redirects when admin exists"""
        response = self.client.get('/admin/setup')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/admin/login'))

    def test_successful_setup(self):
        # Clear session and remove the default admin user
        self.db.session.close()
        self.db.session.query(User).delete()
        self.db.session.commit()
        
        data = {
            'username': 'admin',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        response = self.client.post('/admin/setup', data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/admin/login'))
        
        # Verify admin was created
        admin = UserService.get_admin_user()
        self.assertIsNotNone(admin)
        self.assertEqual(admin.username, 'admin')
        self.assertTrue(admin.is_admin)

    def test_setup_with_json_import(self):
        """Test setup with JSON data import"""
        # Clear session and remove the default admin user
        self.db.session.close()
        self.db.session.query(User).delete()
        self.db.session.commit()
        
        test_data = [
            {
                "id": 1,
                "text": "Test review text",
                "votes_headphones": 0,
                "votes_wine": 1,
                "created_at": "2025-01-25 23:01:18.767771"
            }
        ]
        
        import tempfile
        import json
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as tf:
            json.dump(test_data, tf)
            tf.seek(0)
            
            # Convert the file content to bytes
            file_content = tf.read().encode('utf-8')
            print(f"\nFile content being sent: {file_content}")
            
            data = {
                'username': 'admin',
                'password': 'password123',
                'confirm_password': 'password123',
                'json_file': (BytesIO(file_content), 'test_data.json', 'application/json')
            }
            response = self.client.post('/admin/setup', 
                                      data=data, 
                                      content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/admin/login'))
        
        # Verify imported data
        from app.models.review import Review
        review = Review.query.first()
        self.assertIsNotNone(review, "No review found in database after import")
        self.assertEqual(review.text, "Test review text")
        self.assertEqual(review.votes_wine, 1)
        self.assertEqual(review.votes_headphones, 0) 