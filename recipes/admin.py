from django.contrib import admin
from .models import User, GeneratedRecipe, Recipe, SavedRecipe, SharedRecipe, UserActivity, RecipeRating

# Register your models here.
admin.site.register(User)
admin.site.register(SavedRecipe)
admin.site.register(GeneratedRecipe)
admin.site.register(Recipe)
admin.site.register(SharedRecipe)
admin.site.register(UserActivity)
admin.site.register(RecipeRating)