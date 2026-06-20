from django.urls import path

from apps.settings import views

urlpatterns = [
    path("", views.SettingsOverviewView.as_view(), name="settings-overview"),
    path("navigation/", views.NavigationView.as_view(), name="settings-navigation"),
    path("workspace/", views.WorkspaceSettingsView.as_view(), name="settings-workspace"),
    path("trello/", views.TrelloSettingsView.as_view(), name="settings-trello"),
    path("openai/", views.OpenAISettingsView.as_view(), name="settings-openai"),
]
