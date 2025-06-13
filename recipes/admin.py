from django.contrib import admin
from .models import User, GeneratedRecipe, Recipe, SavedRecipe

# Register your models here.
admin.site.register(User)
admin.site.register(SavedRecipe)
admin.site.register(GeneratedRecipe)
admin.site.register(Recipe)
