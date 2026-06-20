from django.contrib import admin

from integrations.trello.models import (
    Action,
    Board,
    BoardList,
    Card,
    CardStatusHistory,
    EntityHistory,
    Member,
    Snapshot,
)


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("name", "trello_id", "closed", "last_synced_at", "updated_at")
    search_fields = ("name", "trello_id")
    readonly_fields = ("created_at", "updated_at", "last_synced_at")


@admin.register(BoardList)
class BoardListAdmin(admin.ModelAdmin):
    list_display = ("name", "board", "trello_id", "position", "closed")
    list_filter = ("board", "closed")
    search_fields = ("name", "trello_id")


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("full_name", "username", "trello_id")
    search_fields = ("full_name", "username", "trello_id")


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "board",
        "status",
        "is_closed",
        "is_removed",
        "due_at",
        "last_activity_at",
    )
    list_filter = ("board", "status", "is_closed", "is_removed")
    search_fields = ("title", "trello_id", "description")
    filter_horizontal = ("assignees",)


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ("action_type", "board", "member", "occurred_at")
    list_filter = ("board", "action_type")
    search_fields = ("trello_id", "action_type")
    readonly_fields = ("created_at", "updated_at", "raw_json")


@admin.register(CardStatusHistory)
class CardStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("card", "status", "board_list_name", "effective_at", "source")
    list_filter = ("source", "status")
    search_fields = ("card__title", "card__trello_id", "status")
    readonly_fields = ("created_at", "updated_at")


@admin.register(EntityHistory)
class EntityHistoryAdmin(admin.ModelAdmin):
    list_display = ("entity_type", "entity_trello_id", "board", "effective_at", "source")
    list_filter = ("entity_type", "source", "board")
    search_fields = ("entity_trello_id",)
    readonly_fields = ("created_at", "updated_at", "state_json")


@admin.register(Snapshot)
class SnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "board",
        "snapshot_date",
        "card_count",
        "list_count",
        "member_count",
        "action_count",
    )
    list_filter = ("board", "snapshot_date")
    readonly_fields = ("created_at", "updated_at", "state_json")
