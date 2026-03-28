from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from recognition.compare import (
    SYNTHETIC_TEMPLATE_SIGNS,
    ensure_template_file,
    save_template_from_video,
)
from recognition.mediapipe_utils import normalize_sign_name


class Command(BaseCommand):
    help = "Precompute MediaPipe landmark templates for exercise reference signs."

    def add_arguments(self, parser):
        parser.add_argument("--sign", action="append", dest="signs", help="Sign name to build.")
        parser.add_argument(
            "--video",
            action="append",
            nargs=2,
            metavar=("SIGN", "VIDEO_PATH"),
            help="Build a template from a local reference video.",
        )
        parser.add_argument(
            "--synthetic-defaults",
            action="store_true",
            help="Generate the built-in fallback templates for all supported synthetic signs.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace existing template JSON files.",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]
        built_anything = False

        for sign_name, video_path in options.get("video") or []:
            normalized_sign = normalize_sign_name(sign_name)
            path = Path(video_path)
            if not path.exists():
                raise CommandError(f"Video not found: {path}")
            saved_path = save_template_from_video(normalized_sign, path, overwrite=overwrite)
            self.stdout.write(self.style.SUCCESS(f"Built template for {normalized_sign}: {saved_path}"))
            built_anything = True

        synthetic_requested = options.get("synthetic_defaults") or not options.get("video")
        if synthetic_requested:
            requested_signs = options.get("signs") or list(SYNTHETIC_TEMPLATE_SIGNS)
            for sign_name in requested_signs:
                normalized_sign = normalize_sign_name(sign_name)
                saved_path = ensure_template_file(normalized_sign, overwrite=overwrite)
                self.stdout.write(self.style.SUCCESS(f"Prepared template for {normalized_sign}: {saved_path}"))
                built_anything = True

        if not built_anything:
            raise CommandError("No templates were generated. Provide --video or --synthetic-defaults.")
