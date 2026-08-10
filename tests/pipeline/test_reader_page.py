"""Tests for reader.get_page: backend page proxied + manuscript hadith overlay.

get_page combines a proxied consolidated-backend page (raw text, footnote block,
page count) with manuscript.hadiths_for_page (structured hadiths) and the local
chapter title. These pin the mutual-exclusivity contract (hadiths present ->
text_ar None), footnote splitting, total_pages forwarding, and the _fetch_page
status mapping (404 -> ResourceNotFoundError; any other failure ->
ReaderSourceError).
"""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from backend.core.errors import ResourceNotFoundError
from backend.models.reader import Footnote, Hadith
from backend.repositories import reader as reader_repo
from backend.repositories.reader import get_page

_RAW_TEXT = "النص الخام"
_FOOTNOTE_BLOCK = "تتمة من الصفحة السابقة\n(1) الحاشية الأولى"


def _page_dict(
    *,
    text_ar: str | None = _RAW_TEXT,
    footnote_text: str | None = None,
    total_pages: int = 3,
) -> dict[str, object]:
    """A canned consolidated-backend page object, with any field overridden."""
    page: dict[str, object] = {"text_ar": text_ar, "total_pages": total_pages}
    if footnote_text is not None:
        page["footnote_text"] = footnote_text
    return page


def _fake_chapter_title(*_args: object, **_kwargs: object) -> str:
    """An empty chapter title so get_page needs no real TOC source."""
    return ""


def _patch_page(
    monkeypatch: pytest.MonkeyPatch,
    *,
    hadiths: list[Hadith],
    page: dict[str, object] | None = None,
) -> None:
    """Stub _fetch_page + _chapter_title_at + hadiths_for_page for get_page."""

    def fake_fetch(_urn: str, _n: int) -> dict[str, object]:
        """Return the canned backend page so get_page needs no real network."""
        return page if page is not None else _page_dict()

    def fake_hadiths(_urn: str, _page: int) -> list[Hadith]:
        """Return the canned hadith overlay."""
        return hadiths

    monkeypatch.setattr(reader_repo, "_fetch_page", fake_fetch)
    monkeypatch.setattr(reader_repo, "_chapter_title_at", _fake_chapter_title)
    monkeypatch.setattr("backend.repositories.manuscript.hadiths_for_page", fake_hadiths)


def _stub_backend(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[[httpx.Request], httpx.Response],
) -> None:
    """Point reader._fetch_page's client at a mock transport with ``handler``."""
    client = httpx.Client(
        base_url="http://backend.test",
        transport=httpx.MockTransport(handler),
    )
    monkeypatch.setattr(reader_repo, "_backend_client", lambda: client)


def test_should_blank_text_when_hadiths_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the manuscript overlay yields hadiths, text_ar is None."""
    hadith = Hadith(n=1, isnad_ar="الإسناد", matn_ar="المتن", narrators=[])
    _patch_page(monkeypatch, hadiths=[hadith])

    page = get_page("urn:test", 1)

    assert page.hadiths == [hadith]
    assert page.text_ar is None


def test_should_keep_text_when_no_hadiths(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the overlay is empty, the proxied raw text is served."""
    _patch_page(monkeypatch, hadiths=[])

    page = get_page("urn:test", 1)

    assert page.hadiths == []
    assert page.text_ar == _RAW_TEXT


def test_should_forward_total_pages_from_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """total_pages is forwarded from the backend page, not a local row count."""
    _patch_page(monkeypatch, hadiths=[], page=_page_dict(total_pages=42))

    page = get_page("urn:test", 1)

    assert page.total_pages == 42


def test_should_raise_when_total_pages_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """A backend page missing total_pages is a contract violation, surfaced loudly."""
    _patch_page(monkeypatch, hadiths=[], page={"text_ar": _RAW_TEXT})

    with pytest.raises(reader_repo.ReaderSourceError):
        get_page("urn:test", 1)


def test_should_return_empty_when_no_footnotes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A page with no footnote_text yields an empty apparatus list."""
    _patch_page(monkeypatch, hadiths=[])

    page = get_page("urn:test", 1)

    assert page.footnotes == []


def test_should_split_when_footnote_block_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """The proxied footnote_text is split by the canonical splitter."""
    _patch_page(monkeypatch, hadiths=[], page=_page_dict(footnote_text=_FOOTNOTE_BLOCK))

    page = get_page("urn:test", 1)

    assert page.footnotes == [
        Footnote(marker=None, text="تتمة من الصفحة السابقة"),
        Footnote(marker="1", text="الحاشية الأولى"),
    ]


def test_should_carry_footnotes_when_hadiths_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """Footnotes ride on the hadith shape too: they annotate the printed page."""
    hadith = Hadith(n=1, isnad_ar="الإسناد", matn_ar="المتن", narrators=[])
    _patch_page(monkeypatch, hadiths=[hadith], page=_page_dict(footnote_text=_FOOTNOTE_BLOCK))

    page = get_page("urn:test", 1)

    assert page.text_ar is None
    assert [f.marker for f in page.footnotes] == [None, "1"]


def test_should_raise_not_found_when_backend_404(monkeypatch: pytest.MonkeyPatch) -> None:
    """A backend 404 maps to ResourceNotFoundError, a 404 to the client."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Always return 404 so _fetch_page must surface ResourceNotFoundError."""
        return httpx.Response(404)

    _stub_backend(monkeypatch, handler)
    with pytest.raises(ResourceNotFoundError):
        reader_repo._fetch_page("urn:test", 1)


def test_should_raise_when_backend_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-2xx status other than 404 surfaces as ReaderSourceError."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Always return 503 so _fetch_page must surface a backend failure."""
        return httpx.Response(503)

    _stub_backend(monkeypatch, handler)
    with pytest.raises(reader_repo.ReaderSourceError):
        reader_repo._fetch_page("urn:test", 1)


def test_should_raise_when_backend_non_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-JSON body surfaces as ReaderSourceError, never an empty page."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Return a 200 text body so JSON parsing must fail loudly."""
        return httpx.Response(200, content=b"not-json")

    _stub_backend(monkeypatch, handler)
    with pytest.raises(reader_repo.ReaderSourceError):
        reader_repo._fetch_page("urn:test", 1)
