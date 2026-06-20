from django.urls import include, path

urlpatterns = [
    path("trello/", include("apps.integrations.trello.urls")),
]
