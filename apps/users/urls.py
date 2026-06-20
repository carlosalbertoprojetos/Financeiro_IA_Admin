from django.urls import path

from apps.users import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="users-login"),
    path("logout/", views.LogoutView.as_view(), name="users-logout"),
    path("me/", views.CurrentUserView.as_view(), name="users-me"),
    path("permissions/", views.PermissionsView.as_view(), name="users-permissions"),
]
