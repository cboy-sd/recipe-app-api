import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from core import models

from unittest.mock import patch
from django.test import TestCase

from core.models import Recipe, Ingredient, Tag

from rest_framework import status
from rest_framework.test import APIClient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """return the URL for recipe image upload"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    """return recipe detail url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='recipe course'):
    """create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='cinnamon'):
    """create and return ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """" create and return a sample recipe """
    defaults = {
        'title': 'sample Recipe',
        'time_minutes': 10,
        'price': 5.00,
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """test unauthenticated recipe api access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """test that authentication is required"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateApiTests(TestCase):
    """test unauthenticated api access"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'apptest@gmail.com',
            'testpass'
        )
        self.client.force_authenticate(self.user)

    def test_reterive_recipes(self):
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """tags that tags are returned for authenticated user"""
        user2 = get_user_model().objects.create_user(
            'mohamed@gmail.com',
            'testpass',
        )
        sample_recipe(user=self.user)
        sample_recipe(user=user2)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """test viewing recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """test for createing recipe """
        payload = {
            'title': 'chocolatecake',
            'time_minutes': 30,
            'price': 5.00
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """test create recipe with the tags """
        tag1 = sample_tag(user=self.user, name='vagan')
        tag2 = sample_tag(user=self.user, name='dessert')
        payload = {
            'title': 'avocado lime cheese cake',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 60,
            'price': 20.00
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredient(self):
        """test create recipe with ingredient """
        ingredient1 = sample_ingredient(user=self.user, name='pasta')
        ingredient2 = sample_ingredient(user=self.user, name='chicken')
        payload = {
            'title': 'thai pwran red curry',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 40,
            'price': 7.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        """test arecipe with patch """
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='curry')
        payload = {'title': 'chicken tika', 'tags': [new_tag.id]}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_recipe_full_update(self):
        """test updating a recipe with put"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {
            'title': 'spaghetti carbonara',
            'time_minutes': 25,
            'price': 5.00,
        }
        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)

    @patch('uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """test that image is saved in the right location """
        uuid = 'test_uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'myimage.jpg')
        exp_path = f'uploads/recipe/{uuid}.jpg'
        self.assertEqual(file_path, exp_path)


class RecipeUploadImageTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'cboycc@gmail.com',
            'TestPass'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """test that the image is uploaded in to the recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            image = Image.new('RGB', (10, 10))
            image.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')
            self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_image_upload_bad_request(self):
        """test uploading in vaild image """
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""
        recipe1 = sample_recipe(user=self.user, title='Thai vegetable curry')
        recipe2 = sample_recipe(user=self.user, title='Aubergine with tahini')
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Vegetarian')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=self.user, title='Fish and chips')

        res = self.client.get(
            RECIPES_URL,
            {'tags': f'{tag1.id},{tag2.id}'}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """Test returning recipes with specific ingredients"""
        recipe1 = sample_recipe(user=self.user, title='Posh beans on toast')
        recipe2 = sample_recipe(user=self.user, title='Chicken cacciatore')
        ingredient1 = sample_ingredient(user=self.user, name='Feta cheese')
        ingredient2 = sample_ingredient(user=self.user, name='Chicken')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user=self.user, title='Steak and mushrooms')

        res = self.client.get(
            RECIPES_URL,
            {'ingredients': f'{ingredient1.id},{ingredient2.id}'}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
