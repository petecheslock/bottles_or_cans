from tests.base import BaseTestCase
from app.services.user import UserService
from app.models.user import User

class TestUserService(BaseTestCase):
    def test_create_admin(self):
        user = UserService.create_admin('new_admin', 'password123')
        self.assertTrue(user.is_admin)
        self.assertEqual(user.username, 'new_admin')
        self.assertTrue(user.check_password('password123'))

    def test_change_admin_password(self):
        # Test successful password change
        result = UserService.change_admin_password(
            self.admin.id,
            'test_password',  # Current password
            'new_password',
            'new_password'
        )
        self.assertTrue(result)
        self.assertTrue(self.admin.check_password('new_password'))

        # Test failed password change - wrong current password
        result = UserService.change_admin_password(
            self.admin.id,
            'wrong_password',
            'new_password2',
            'new_password2'
        )
        self.assertFalse(result)

        # Test failed password change - passwords don't match
        result = UserService.change_admin_password(
            self.admin.id,
            'new_password',
            'newer_password',
            'different_password'
        )
        self.assertFalse(result) 