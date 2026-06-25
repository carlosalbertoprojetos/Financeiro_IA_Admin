import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.intelligence.services.report_query.domain.dsl_parser import parse_report_dsl
from apps.intelligence.services.report_query.domain.filters import ReportQueryPayload
from apps.intelligence.services.report_query.engine.executor import execute_report_query
from apps.intelligence.services.report_query.diagnose import diagnose_board_filters
from apps.intelligence.services.report_query.presets import PRESETS


class Command(BaseCommand):
    help = (
        "Generate a segmented report from combined filters. "
        "Use --preset executive-aqui for the default executive [AQUI] report."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--board-id",
            type=str,
            required=True,
            help="Trello board ID (required)",
        )
        parser.add_argument(
            "--preset",
            type=str,
            choices=list(PRESETS.keys()),
            help="Use a built-in report preset (e.g. executive-aqui)",
        )
        parser.add_argument(
            "--dsl",
            type=str,
            help="Inline report DSL text",
        )
        parser.add_argument(
            "--dsl-file",
            type=str,
            help="Path to a .dsl or .txt file with report DSL",
        )
        parser.add_argument(
            "--output",
            type=str,
            help="Write JSON result to this file",
        )
        parser.add_argument(
            "--no-cache",
            action="store_true",
            help="Bypass report cache",
        )
        parser.add_argument(
            "--diagnose",
            action="store_true",
            help="Show board data samples to help tune filters (no report generated)",
        )
        parser.add_argument(
            "--generated-by",
            type=str,
            default="cli",
            help="Audit log user identifier",
        )

    def handle(self, *args, **options):
        board_id = options["board_id"]

        if options.get("diagnose"):
            result = diagnose_board_filters(board_id)
            self.stdout.write(json.dumps(result, indent=2, ensure_ascii=False))
            if result.get("error"):
                raise CommandError(result["error"])
            return

        dsl_text = self._resolve_dsl(options)

        parsed = parse_report_dsl(dsl_text)
        parsed["board_id"] = board_id
        parsed["use_cache"] = not options["no_cache"]
        parsed["generated_by"] = options["generated_by"]

        try:
            payload = ReportQueryPayload.from_dict(parsed)
        except (ValueError, KeyError) as exc:
            raise CommandError(f"Invalid report query: {exc}") from exc

        self.stdout.write(f"Running report {payload.report_type.value} for board {board_id}...")

        try:
            result = execute_report_query(payload)
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        meta = result.get("meta", {})
        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {meta.get('matched_cards', 0)} matched, "
                f"{meta.get('returned_cards', 0)} returned, "
                f"{meta.get('processing_ms', 0)}ms"
                f"{' (cache hit)' if meta.get('cache_hit') else ''}"
            )
        )

        if result.get("metrics"):
            self.stdout.write("Metrics summary:")
            self.stdout.write(json.dumps(result["metrics"], indent=2, ensure_ascii=False))

        if result.get("grouped"):
            self.stdout.write("Grouped summary:")
            self.stdout.write(json.dumps(result["grouped"], indent=2, ensure_ascii=False))

        if meta.get("matched_cards", 0) == 0:
            self.stdout.write(
                self.style.WARNING(
                    "0 cards matched. Run with --diagnose to inspect labels, prefixes and members."
                )
            )
            diag = diagnose_board_filters(board_id)
            if diag.get("available_boards"):
                self.stdout.write(f"Available boards: {diag['available_boards']}")
            elif diag.get("top_title_prefixes"):
                self.stdout.write(f"Title prefixes in board: {diag['top_title_prefixes'][:8]}")
                self.stdout.write(f"Labels in board: {diag['top_labels'][:8]}")
                self.stdout.write(f"Members: {[m['full_name'] for m in diag.get('members', [])[:8]]}")

        cards = result.get("cards", [])
        if cards:
            self.stdout.write(f"\nTop cards (by {meta.get('sort', {}).get('by', 'RISK_SCORE')}):")
            for card in cards[:10]:
                self.stdout.write(
                    f"  - [{card.get('risk_score', '?')}] {card.get('title', '')[:70]}"
                )

        output_path = options.get("output")
        if output_path:
            path = Path(output_path)
            path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Full report saved to {path}"))
        else:
            self.stdout.write("\nTip: use --output report.json to save the full response.")

    def _resolve_dsl(self, options) -> str:
        if options.get("dsl_file"):
            path = Path(options["dsl_file"])
            if not path.exists():
                raise CommandError(f"DSL file not found: {path}")
            return path.read_text(encoding="utf-8")

        if options.get("dsl"):
            return options["dsl"]

        preset = options.get("preset")
        if preset:
            return PRESETS[preset]

        raise CommandError(
            "Provide --preset executive-aqui, --dsl '...', or --dsl-file path/to/query.dsl"
        )
