"""Artifact build layer — materializes sol-next2's read-only data artifacts.

The WRITE side of the data contract: schemas, bulk-insert statements, and row
projections that turn the upstream corpus into ``data/manuscript.db`` (span/entity/unit), ``data/registry.db``, and
``data/books_index.json``. The shared machinery (artifact lifecycle, catalog
build loop, CLI shell) lives in ``backend.build.runner``; each artifact module
owns only its schema + projections. The READ side (the served queries) lives in
``backend.repositories``; splitting write-from-read keeps the serving
repositories pure read-only. CENTRAL-005 permits raw SQL here.
"""
