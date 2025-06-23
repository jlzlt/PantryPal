from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("shared/", views.shared, name="shared"),
    path("about/", views.about, name="about"),
    path("saved/", views.saved, name="saved"),
    path("save_recipe/", views.save_recipe, name="save_recipe"),
    path("remove_saved_recipe/", views.remove_saved_recipe, name="remove_saved_recipe"),
    path(
        "autocomplete_ingredients/", views.autocomplete_ingredients, name="autocomplete"
    ),
    path("recipe/<int:recipe_id>/", views.recipe_details, name="recipe_details"),
    path("share_recipe/", views.share_recipe, name="share_recipe"),
    path("remove_shared_recipe/", views.remove_shared_recipe, name="remove_shared_recipe"),
    path("rate/<int:shared_recipe_id>/", views.rate_recipe, name="rate_recipe"),
]
