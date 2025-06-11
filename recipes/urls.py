from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("trending/", views.trending, name="trending"),
    path("about/", views.about, name="about"),
    path("saved/", views.saved, name="saved"),
    path("save_recipe/", views.save_recipe, name="save_recipe"),
    path("remove_saved_recipe/", views.remove_saved_recipe, name="remove_saved_recipe"),
    path(
        "autocomplete_ingredients/", views.autocomplete_ingredients, name="autocomplete"
    ),
]
