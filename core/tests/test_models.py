from django.contrib.auth import get_user_model
from django.test import TestCase

from core import models
from core.models import Ingredient


def sample_user(email='cboy222@gmaTagil.com', password='hellomrcboy'):
    """create a sample user"""
    return get_user_model().objects.create_user(email, password)


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
        """to verify that email address is valid"""
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

    def test_tag_str(self):
        """ test that tag is string  representation"""
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Vegan',
        )
        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """test that ingredient is string"""
        ingredient = Ingredient.objects.create(
            user=sample_user(),
            name='cucumber',
        )
        self.assertEqual(str(ingredient), ingredient.name)
