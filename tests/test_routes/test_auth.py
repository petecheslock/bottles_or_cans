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