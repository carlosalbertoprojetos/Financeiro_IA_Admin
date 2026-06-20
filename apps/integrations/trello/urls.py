from django.urls import path

from apps.integrations.trello import views

urlpatterns = [
    path("connect/", views.TrelloConnectView.as_view(), name="trello-connect"),
    path(
        "connections/<str:connection_id>/workspaces/",
        views.TrelloWorkspacesView.as_view(),
        name="trello-workspaces",
    ),
    path(
        "connections/<str:connection_id>/boards/",
        views.TrelloBoardsView.as_view(),
        name="trello-boards",
    ),
    path(
        "connections/<str:connection_id>/sync/",
        views.TrelloSyncView.as_view(),
        name="trello-sync-connection",
    ),
]
