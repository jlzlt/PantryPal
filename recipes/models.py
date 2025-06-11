from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)


class SavedRecipe(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="saved", blank=False, null=False
    )
    title = models.CharField(max_length=255, blank=False, null=False)
    ingredients = models.TextField(blank=False, null=False)
    instructions = models.TextField(blank=False, null=False)
    meal_photo = models.ImageField(
        upload_to="media/shared_meals/", blank=True, null=True
    )
    tags = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class SharedRecipe(models.Model):
    original = models.ForeignKey(
        SavedRecipe,
        on_delete=models.CASCADE,
        related_name="shared",
        blank=False,
        null=False,
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shared", blank=False, null=False
    )
    shared_at = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    user_comment = models.TextField()
    meal_photo = models.ImageField(upload_to="media/shared_meals/")


class RecipeComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False)
    recipe = models.ForeignKey(
        SharedRecipe,
        on_delete=models.CASCADE,
        related_name="comments",
        blank=False,
        null=False,
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class RecipeVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False)
    recipe = models.ForeignKey(
        SharedRecipe, on_delete=models.CASCADE, blank=False, null=False
    )
    vote = models.SmallIntegerField(blank=False, null=False)
