from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import timedelta
from django.utils.timezone import now
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    email = models.EmailField(unique=True)


class GeneratedRecipe(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="generated_recipes"
    )
    title = models.CharField(max_length=255, blank=False, null=False)
    ingredients = models.JSONField(blank=False, null=False)
    instructions = models.JSONField(blank=False, null=False)
    tags = models.JSONField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def is_expired(self):
        return self.created_at < now() - timedelta(hours=24)

    def __str__(self):
        return f"#{self.id} {self.title} by {self.user}"


class Recipe(models.Model):
    title = models.CharField(max_length=255, blank=False, null=False)
    ingredients = models.JSONField(blank=False, null=False)
    instructions = models.JSONField(blank=False, null=False)
    tags = models.JSONField(blank=True, null=True)
    image = models.ImageField(upload_to="recipes/", blank=True, null=True)
    hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.id} {self.title}"

    class Meta:
        ordering = ["-created_at"]


class SavedRecipe(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="saved_recipes"
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="saved_by_users"
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "recipe")
        ordering = ["-saved_at"]

    def __str__(self):
        return f"#{self.id} {self.recipe.title} saved by {self.user}"


class SharedRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="shared_versions"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shared_recipes"
    )
    user_comment = models.TextField(blank=True, null=True)
    user_photo = models.ImageField(upload_to="shared_photos/", blank=True, null=True)
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-shared_at"]

    def __str__(self):
        return f"#{self.id} {self.recipe.title} shared by {self.user}"

    def get_average_rating(self):
        ratings = self.ratings.all()
        if not ratings:
            return None
        return round(sum(r.rating for r in ratings) / len(ratings), 1)


class RecipeComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        SharedRecipe, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField(blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.recipe}"


class RecipeRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        SharedRecipe, on_delete=models.CASCADE, related_name="ratings"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )  # 1 to 5

    class Meta:
        unique_together = ("user", "recipe")

    def __str__(self):
        return f"Rating {self.rating}/5 by {self.user} on {self.recipe}"
