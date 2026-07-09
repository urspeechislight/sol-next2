"""Tests for identity clustering: distinct men who share a nasab must not fuse."""

from __future__ import annotations

from backend.build.authority import _cluster_by_full_name, _split_by_death


def _entries(*names: str) -> list[dict[str, str]]:
    return [{"full_name": n} for n in names]


def test_should_split_nasab_by_tail() -> None:
    """Same nasab, incompatible nisbas -> separate men; prefix variants collapse."""
    entries = _entries(
        "أحمد بن محمد بن عيسى الأشعري القمي",
        "أحمد بن محمد بن عيسى الأشعري",
        "أحمد بن محمد بن عيسى العلوي الحسيني",
        "أحمد بن محمد بن عيسى",
    )
    clusters = _cluster_by_full_name(entries)
    names = {tuple(sorted(e["full_name"] for e in c)) for c in clusters}
    assert len(clusters) == 3
    assert (
        "أحمد بن محمد بن عيسى الأشعري",
        "أحمد بن محمد بن عيسى الأشعري القمي",
    ) in names
    assert ("أحمد بن محمد بن عيسى العلوي الحسيني",) in names
    assert ("أحمد بن محمد بن عيسى",) in names


def test_should_merge_name_prefixes() -> None:
    """A single man whose name grows across sources stays one cluster (all prefixes)."""
    entries = _entries(
        "سفيان بن عيينة",
        "سفيان بن عيينة الهلالي",
        "سفيان بن عيينة الهلالي الكوفي",
    )
    assert len(_cluster_by_full_name(entries)) == 1


def test_should_crop_waw_co_narrator() -> None:
    """A wāw-joined entry clusters under its first person, not a fused pair."""
    entries = _entries(
        "أحمد بن محمد بن عيسى الأشعري",
        "أحمد بن محمد بن عيسى وسهل بن زياد",
    )
    clusters = _cluster_by_full_name(entries)
    assert len(clusters) == 1


def test_should_remerge_one_mans_nisbas() -> None:
    """Different nisbas of one man re-merge when they share two or more teachers."""
    entries = [
        {"full_name": "سفيان بن عيينة الهلالي", "teacher_names": ["الزهري", "عمرو بن دينار"]},
        {"full_name": "سفيان بن عيينة الكوفي", "teacher_names": ["الزهري", "عمرو بن دينار"]},
    ]
    assert len(_cluster_by_full_name(entries)) == 1


def test_should_keep_distinct_men_apart() -> None:
    """Men sharing a nasab but not teachers or death year are not re-merged."""
    entries = [
        {"full_name": "أحمد بن محمد بن عيسى الأشعري", "teacher_names": ["الحسين بن سعيد"]},
        {"full_name": "أحمد بن محمد بن عيسى العلوي", "teacher_names": ["إبراهيم بن هاشم"]},
    ]
    assert len(_cluster_by_full_name(entries)) == 2


def _dated(death: int | None, teachers: tuple[str, ...] = ()) -> dict[str, object]:
    return {"full_name": "محمد بن عبد الله", "death_year": death, "teacher_names": list(teachers)}


def test_should_split_a_bare_cluster_on_incompatible_deaths() -> None:
    """Same bare name, death-years centuries apart -> distinct men."""
    assert len(_split_by_death([_dated(177), _dated(450)])) == 2


def test_should_keep_a_bare_cluster_within_the_death_tolerance() -> None:
    """Deaths a few years apart are one man whose sources disagree."""
    assert len(_split_by_death([_dated(198), _dated(200)])) == 1


def test_should_keep_an_undated_bare_cluster_as_one_person() -> None:
    """With no death-year there is no evidence to split on."""
    assert len(_split_by_death([_dated(None), _dated(None)])) == 1


def test_should_attach_an_undated_entry_to_the_sole_dated_person() -> None:
    """One dated person plus an undated entry stays one person, not a residual."""
    assert len(_split_by_death([_dated(200), _dated(None)])) == 1


def test_should_route_an_undated_entry_to_its_teacher_match() -> None:
    """With several dated people an undated entry joins the one it shares a teacher with."""
    cluster = [_dated(100, ("أ",)), _dated(400, ("ب",)), _dated(None, ("أ",))]
    assert len(_split_by_death(cluster)) == 2


def test_should_pool_an_unplaceable_undated_entry_as_a_residual() -> None:
    """An undated entry matching no dated person's teachers becomes its own residual."""
    cluster = [_dated(100, ("أ",)), _dated(400, ("ب",)), _dated(None, ("ج",))]
    assert len(_split_by_death(cluster)) == 3
