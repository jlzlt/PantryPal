from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Recipe, SavedRecipe, SharedRecipe, GeneratedRecipe, RecipeRating, UserActivity
from django.core.files.uploadedfile import SimpleUploadedFile
import json

User = get_user_model()

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.user2 = User.objects.create_user(username='otheruser', email='other@example.com', password='testpass456')
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            ingredients=["bread", "cheese", "butter"],
            instructions=["Step 1", "Step 2"],
            tags=["quick", "easy_only"],
            hash='hash123',
        )
        self.shared_recipe = SharedRecipe.objects.create(recipe=self.recipe, author=self.user)
        self.saved_recipe = SavedRecipe.objects.create(user=self.user, recipe=self.recipe)
        self.gen_recipe = GeneratedRecipe.objects.create(
            user=self.user,
            title='Generated',
            ingredients=["bread"],
            instructions=["Step 1"],
            tags=["quick"],
            image_url='',
            hash='genhash',
        )

    def test_index_view_get(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/index.html')

    def test_register_view(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'confirmation': 'newpass123',
        })
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_logout_view(self):
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'testpass123'})
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_shared_view(self):
        response = self.client.get(reverse('shared'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/shared.html')

    def test_about_view(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/about.html')

    def test_autocomplete_ingredients(self):
        response = self.client.get(reverse('autocomplete'), {'query': 'brea'})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_recipe_details_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('recipe_details', args=[self.recipe.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/recipe_details.html')

    def test_saved_view_requires_login(self):
        response = self.client.get(reverse('saved'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('saved'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/saved.html')

    def test_save_recipe_post(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('save_recipe'), {'recipe_hash': self.recipe.hash})
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()['status'], ['saved', 'exists'])

    def test_save_recipe_missing_hash(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('save_recipe'), {})
        self.assertEqual(response.status_code, 400)

    def test_remove_saved_recipe(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('remove_saved_recipe'), {'recipe_hash': self.recipe.hash})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'removed')

    def test_remove_saved_recipe_not_found(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('remove_saved_recipe'), {'recipe_hash': 'notfound'})
        self.assertEqual(response.status_code, 404)

    def test_share_recipe(self):
        self.client.login(username='testuser', password='testpass123')
        # Unshare first to allow sharing
        SharedRecipe.objects.filter(recipe=self.recipe, author=self.user).delete()
        response = self.client.post(reverse('share_recipe'), {'recipe_id': self.recipe.id})
        self.assertIn(response.status_code, [302, 200])

    def test_remove_shared_recipe(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('remove_shared_recipe'), {'recipe_id': self.recipe.id})
        self.assertIn(response.status_code, [302, 200])

    def test_rate_recipe(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('rate_recipe', args=[self.shared_recipe.id]), {'rating': 5})
        self.assertIn(response.status_code, [302, 200])
        self.assertTrue(RecipeRating.objects.filter(rater=self.user, recipe=self.shared_recipe).exists())

    def test_profile_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recipes/profile.html')

    def test_profile_update_email(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('profile'), {'email': 'newemail@example.com', 'email_submit': '1'})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIn('recipes/profile.html', [t.name for t in response.templates])

    def test_profile_update_password(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('profile'), {
            'old_password': 'testpass123',
            'new_password1': 'newpass1234',
            'new_password2': 'newpass1234',
            'password_submit': '1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('recipes/profile.html', [t.name for t in response.templates])
