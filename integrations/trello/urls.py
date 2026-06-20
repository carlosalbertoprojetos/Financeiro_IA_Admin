from django.urls import path

from integrations.trello.views import SyncBoardView

urlpatterns = [
    path("sync/<str:board_id>/", SyncBoardView.as_view(), name="trello-sync-board"),
]
