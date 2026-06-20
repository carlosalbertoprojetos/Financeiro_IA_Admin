from django.core.management.base import BaseCommand, CommandError

from integrations.trello.exceptions import TrelloAPIError
from integrations.trello.services.sync import sync_board


class Command(BaseCommand):
    help = "Sync a Trello board into PostgreSQL (boards, lists, cards, actions, members, snapshots)."

    def add_arguments(self, parser):
        parser.add_argument("board_id", type=str, help="Trello board ID")

    def handle(self, *args, **options):
        board_id = options["board_id"]

        try:
            result = sync_board(board_id)
        except TrelloAPIError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Synced board '{result.board_name}' ({result.board_id}): "
                f"{result.cards} cards, {result.lists} lists, "
                f"{result.members} members, {result.actions} new actions, "
                f"{result.removed_cards} removed, "
                f"{result.status_history_entries} status history, "
                f"{result.entity_history_entries} entity history, "
                f"snapshot_created={result.snapshot_created}."
            )
        )
