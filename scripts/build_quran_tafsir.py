#!/usr/bin/env python3
"""Stage 1 driver: gather per-verse tafsir candidates to an intermediate JSON.

Thin CLI wrapper around ``backend.build.quran_tafsir.gather_candidates``. Writes
the candidates to ``/tmp`` (an intermediate artifact, NOT ``data/``) for the
Stage 2 LLM judge to consume. Run from the repo root::

    uv run python scripts/build_quran_tafsir.py --surah 1
    uv run python scripts/build_quran_tafsir.py --surah 1 --out /tmp/x.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any, cast

from backend.build import quran_tafsir
from backend.core.constants import QURAN__SURAH_COUNT
from backend.core.logging import configure_logging, get_logger

_DEFAULT_OUT = Path("/tmp/quran_tafsir_candidates.json")  # noqa: S108
_logger = get_logger("shia-library.build.quran-tafsir")


def _build(args: argparse.Namespace) -> dict[str, object]:
    """Gather candidates for the requested surah and write them to ``args.out``."""
    payload = asyncio.run(quran_tafsir.gather_candidates(args.surah))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    verses = cast(list[dict[str, Any]], payload["verses"])
    n_candidates = sum(len(verse.get("candidates", [])) for verse in verses)
    return {
        "surah": args.surah,
        "verses": len(verses),
        "candidates": n_candidates,
        "out": str(args.out),
    }


def main() -> None:
    """Parse args, time the gather, and log one build-complete report."""
    configure_logging()
    parser = argparse.ArgumentParser(
        description="Gather Stage 1 per-verse tafsir candidates to an intermediate JSON file."
    )
    parser.add_argument("--surah", type=int, required=True, help="surah number, 1..114")
    parser.add_argument(
        "--out", type=Path, default=_DEFAULT_OUT, help="output JSON path (default /tmp)"
    )
    args = parser.parse_args()
    if not 1 <= args.surah <= QURAN__SURAH_COUNT:
        parser.error(f"--surah must be between 1 and {QURAN__SURAH_COUNT}")
    start = time.monotonic()
    report = _build(args)
    _logger.info("build-complete", elapsed_s=round(time.monotonic() - start), **report)


if __name__ == "__main__":
    main()
