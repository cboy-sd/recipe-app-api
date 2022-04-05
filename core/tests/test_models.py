from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):

    def test_create_user(self):
        """test create new user with email and password successful """
        email = "mohamed@gmail.com"
        password = "Test123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalize(self):
        """test for new user email is  normalize """
        email = "'MOHAMED@GMAIL.COM"
        user = get_user_model().objects.create_user(email, 'Test123')

        self.assertTrue(user.email, email.lower())

    def test_new_invalid_user_email(self):
        """to verify that email address is valid and the email field is not blank"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, "Test123")

    def test_create_new_super_user(self):
        """ create supper user testing function """
        user = get_user_model().objects.create_superuser(
            "cboyc@gmail.com",
            "helloworld1223@"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
