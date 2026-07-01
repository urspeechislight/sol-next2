"""Isnad-continuation boundary merging for the segment phase (façade).

Re-export front over _boundaries_regex (config-driven regex builders) and
_boundaries_merge (the per-paragraph merge logic), split from sol-next's single
boundaries.py to stay under the file-size cap. The segment phase imports
MergeCues, build_merge_params_from_config, and merge_isnad_continuations here.
"""

from __future__ import annotations

from backend.pipeline._boundaries_merge import MergeCues, merge_isnad_continuations
from backend.pipeline._boundaries_regex import build_merge_params_from_config

__all__ = ["MergeCues", "build_merge_params_from_config", "merge_isnad_continuations"]
