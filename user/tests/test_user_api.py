from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """ test the user api public """

    def Setup(self):
        self.client = APIClient

    def test_create_user_valid_success(self):
        """ test create user with valid payload successfuly """
        payload = {
            'email': 'cboyc22@gmail.com',
            'password': 'Test123',
            'name': 'mrcboy',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)

        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """ test that creating exists user fails """
        payload = {'email': 'cboyc22@gmail.com', 'password': 'Test123'}
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, **payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """ test that password is more than 5 characters """

        payload = {'email': 'cboyc22@gmail.com', 'password': 'pw'}
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """test that stoken is created for the user user"""
        payload = {'email': 'cboydola@gmail.com', 'password': 'himrboy@'}
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """test that token is  not created if invalid credentials are given  """
        create_user(email='cbyc222@gmail.com', password='mrcboy2')
        payload = {'email': 'cboyc222@gmail.com', 'password': 'wrongnamba'}

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """"test that token is not created if  user is not exists"""
        payload = {'email': 'himrcboy@gmial.com', 'password': 'himrmohamed12'}
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """ test that missing """
        res = self.client.post(TOKEN_URL, {'email': 'one', 'password': ''})
        self.assertNotIn('token', res.data)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
