from django.test import TestCase
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            phone='+234812345678',
            city='Lagos',
            country='Nigeria'
        )

    def test_user_profile_creation(self):
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.city, 'Lagos')

    def test_user_profile_string_representation(self):
        expected = f"{self.user.username}'s Profile"
        self.assertEqual(str(self.profile), expected)
