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
    path(
        "autocomplete_ingredients/", views.autocomplete_ingredients, name="autocomplete"
    ),
]
