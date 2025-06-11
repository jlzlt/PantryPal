from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)


class SavedRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved")
    title = models.CharField(max_length=255, blank=False, null=False)
    ingredients = models.JSONField(blank=False, null=False)
    instructions = models.JSONField(blank=False, null=False)
    tags = models.JSONField(blank=True, null=True)
    image = models.ImageField(upload_to="shared_meals/", blank=True, null=True)
    hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"id: {self.id} title: {self.title}"


class SharedRecipe(models.Model):
    original = models.ForeignKey(
        SavedRecipe, on_delete=models.CASCADE, related_name="shared"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shared")
    shared_at = models.DateTimeField(auto_now_add=True, blank=False, null=False)
    user_comment = models.TextField()
    meal_photo = models.ImageField(upload_to="media/shared_meals/")


class RecipeComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        SharedRecipe,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class RecipeVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(SharedRecipe, on_delete=models.CASCADE)
    vote = models.SmallIntegerField(blank=False, null=False)
