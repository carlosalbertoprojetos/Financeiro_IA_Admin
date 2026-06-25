"""
POCL — Pilot Operational Control Loop management command.

Usage:
  python manage.py pocl activate --board-id ID --team "Ops Team"
  python manage.py pocl stream --board-id ID
  python manage.py pocl cycle --board-id ID --phase morning
  python manage.py pocl followups --board-id ID
  python manage.py pocl report --board-id ID
  python manage.py pocl evaluate --board-id ID
  python manage.py pocl status --board-id ID
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.intelligence.services.pilot.config import activate_pilot, pilot_status_summary
from apps.intelligence.services.pilot.daily_cycle import run_daily_cycle
from apps.intelligence.services.pilot.decision_stream import run_decision_stream
from apps.intelligence.services.pilot.evaluation import compute_pilot_metrics, generate_pilot_evaluation_report
from apps.intelligence.services.pilot.impact_tracker import process_due_followups
from apps.intelligence.services.pilot.report_generator import generate_executive_daily_report
from apps.intelligence.services.pilot.config import get_active_pilot


class Command(BaseCommand):
    help = "Pilot Operational Control Loop — activate and run controlled operational pilot."

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["activate", "stream", "cycle", "followups", "report", "evaluate", "status"],
        )
        parser.add_argument("--board-id", type=str, default="")
        parser.add_argument("--team", type=str, default="Operations")
        parser.add_argument("--board-name", type=str, default="")
        parser.add_argument("--phase", type=str, default="morning", choices=["morning", "intraday", "eod"])
        parser.add_argument("--duration-days", type=int, default=10)
        parser.add_argument("--no-sync", action="store_true")
        parser.add_argument("--limit", type=int, default=20)

    def handle(self, *args, **options):
        action = options["action"]
        board_id = options["board_id"]

        if action == "activate":
            if not board_id:
                raise CommandError("--board-id required")
            pilot = activate_pilot(
                board_id=board_id,
                team_name=options["team"],
                board_name=options["board_name"],
                duration_days=options["duration_days"],
            )
            self.stdout.write(self.style.SUCCESS(
                f"Pilot activated: board={pilot.board_id} team={pilot.team_name} until {pilot.ends_at}",
            ))
            return

        if not board_id:
            raise CommandError("--board-id required")

        if action == "stream":
            result = run_decision_stream(board_id, trigger="cli", limit=options["limit"])
        elif action == "cycle":
            result = run_daily_cycle(
                board_id,
                phase=options["phase"],
                trigger="cli",
                sync=not options["no_sync"],
            )
        elif action == "followups":
            result = process_due_followups(board_id=board_id)
        elif action == "report":
            pilot = get_active_pilot(board_id=board_id)
            path = generate_executive_daily_report(board_id=board_id, pilot=pilot)
            self.stdout.write(self.style.SUCCESS(f"Report written to {path}"))
            return
        elif action == "evaluate":
            metrics = compute_pilot_metrics(board_id=board_id)
            path = generate_pilot_evaluation_report(board_id=board_id)
            self.stdout.write(f"Metrics: {metrics}")
            self.stdout.write(self.style.SUCCESS(f"Evaluation report: {path}"))
            return
        elif action == "status":
            result = {**pilot_status_summary(board_id=board_id), "metrics": compute_pilot_metrics(board_id=board_id)}
        else:
            raise CommandError(f"Unknown action: {action}")

        self.stdout.write(str(result))
