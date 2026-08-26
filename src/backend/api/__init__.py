"""API routers — every HTTP route decorator lives under this package.

``centralization`` (CENTRAL-004) blocks ``@router.*`` / ``@app.*`` decorators
outside ``src/backend/api/`` and ``main.py``. Adding a new resource means
adding a new ``<resource>.py`` here and registering its router below.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.almanac import router as almanac_router
from backend.api.books import router as books_router
from backend.api.citations import router as citations_router
from backend.api.daily import router as daily_router
from backend.api.domains import router as domains_router
from backend.api.extraction import router as extraction_router
from backend.api.quran import router as quran_router
from backend.api.reader import router as reader_router
from backend.api.rijal import router as narrators_router
from backend.api.search import router as search_router
from backend.api.works import router as works_router

api_router = APIRouter()
api_router.include_router(domains_router)
api_router.include_router(books_router)
api_router.include_router(works_router)
api_router.include_router(reader_router)
api_router.include_router(daily_router)
api_router.include_router(almanac_router)
api_router.include_router(narrators_router)
api_router.include_router(citations_router)
api_router.include_router(search_router)
api_router.include_router(quran_router)
api_router.include_router(extraction_router)
