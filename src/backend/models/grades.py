"""Shared editorial vocabulary for hadith grading.

One definition of ``HadithGrade``, imported by the reader DTOs (per-hadith
grade) and the daily editorial DTOs, so the grade vocabulary lives once.
"""

from __future__ import annotations

from typing import Literal

HadithGrade = Literal["sahih", "hasan", "daif", "mawdu"]
