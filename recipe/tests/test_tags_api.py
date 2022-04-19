from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from core.models import Tag, Recipe

from rest_framework import status
from rest_framework.test import APIClient

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    """Test the publicly available tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login required for retrieving tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """test the authorized user for tag api"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'mrhamanam@gmail.com',
            'mrcbo2334',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_reterive_tags_list(self):
        """test that reterive list of tags"""
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="dimber")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """tags that tags are returned for authenticated user"""
        user2 = get_user_model().objects.create_user(
            'mohamed@gmail.com',
            'testpass',
        )
        Tag.objects.create(user=user2, name='fruity')
        tag = Tag.objects.create(user=self.user, name='comfort food')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_tag_created_successfully(self):
        """test that tag is created successfully"""
        payload = {'name': 'Test Tag'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)

    def test_create_invalid_tag(self):
        """test create a new tag with in valid payload """
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """test filter that only returns assigned tags"""
        tag1 = Tag.objects.create(user=self.user, name='breakfast')
        tag2 = Tag.objects.create(user=self.user, name='lunch')
        recipe = Recipe.objects.create(
            title='coriander eggs with toast',
            time_minutes=10,
            price=4.00,
            user=self.user,
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        """test filtering tags by assigned returns unique items"""
        tag = Tag.objects.create(user=self.user, name='breakfast')
        Tag.objects.create(user=self.user, name='lunch')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='pancakes',
            time_minutes=3,
            price=3.00
        )
        recipe1.tags.add(tag)

        recipe2 = Recipe.objects.create(
            user=self.user,
            title='porridge',
            time_minutes=3,
            price=7.00
        )
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
