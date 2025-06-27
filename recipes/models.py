from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now
from django.core.validators import MinValueValidator, MaxValueValidator

User = AbstractUser


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
    image_url = models.URLField(max_length=500, blank=True, null=True)
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
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shared_recipes"
    )
    user_comment = models.TextField(blank=True, null=True)
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-shared_at"]

    def __str__(self):
        return f"#{self.id} {self.recipe.title} shared by {self.author}"

    def get_average_rating(self):
        ratings = self.ratings.all()
        if not ratings:
            return None
        return round(sum(r.rating for r in ratings) / len(ratings), 1)

    def get_total_votes(self):
        return self.ratings.count()


class RecipeComment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        SharedRecipe, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField(blank=False, null=False)
    image = models.ImageField(upload_to="comment_photos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.recipe}"


class RecipeRating(models.Model):
    rater = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        SharedRecipe, on_delete=models.CASCADE, related_name="ratings"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )  # 1 to 5

    class Meta:
        unique_together = ("rater", "recipe")

    def __str__(self):
        return f"Rating {self.rating}/5 by {self.rater} on {self.recipe}"


class UserActivity(models.Model):
    ACTION_CHOICES = [
        ('generated', 'Generated'),
        ('saved', 'Saved Recipe'),
        ('shared', 'Shared Recipe'),
        ('unshared', 'Unshared Recipe'),
        ('unsaved', 'Unsaved Recipe'),
        ('commented', 'Commented'),
        ('rated', 'Rated Recipe'),
        ('email_changed', 'Changed Email'),
        ('password_changed', 'Changed Password'),
    ]
    user = models.ForeignKey('recipes.User', on_delete=models.CASCADE, related_name='activities')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp} {self.user.username} {self.action} {self.details}"
