from django.urls import include, path

from apps.data_sources import trello_views, views

urlpatterns = [
    path("", views.DataSourcesOverviewView.as_view(), name="data-sources-overview"),
    path("trello/connect/", trello_views.DataSourceTrelloConnectView.as_view(), name="ds-trello-connect"),
    path("trello/sync/", trello_views.DataSourceTrelloSyncView.as_view(), name="ds-trello-sync"),
    path("trello/status/", trello_views.DataSourceTrelloStatusView.as_view(), name="ds-trello-status"),
    path("trello/", include("integrations.trello.urls")),
    path("excel/", views.ExcelImportPlaceholderView.as_view(), name="data-sources-excel"),
]
