from django.contrib import admin
from .models import User, SavedRecipe

# Register your models here.
admin.site.register(User)
admin.site.register(SavedRecipe)
