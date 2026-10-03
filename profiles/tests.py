from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from testimonials.models import testimonial


User = get_user_model()


class ProfileTestimonialSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user',
            email='test_user@example.com',
            password='TestPassword123!',
        )

        self.client.force_login(self.user)

    def test_user_cannot_submit_testimonial_to_own_profile(self):
        profile_url = reverse(
            'profile',
            kwargs={'username': self.user.username},
        )

        response = self.client.post(
            profile_url,
            {'content': 'Self-written testimonial'},
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            testimonial.objects.filter(
                author=self.user,
                recipient=self.user,
            ).exists()
        )