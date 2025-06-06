from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path(
        "autocomplete_ingredients/", views.autocomplete_ingredients, name="autocomplete"
    ),
]
