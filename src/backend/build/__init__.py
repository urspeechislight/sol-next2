"""Artifact build layer — materializes sol-next2's read-only SQLite artifacts.

The WRITE side of the data contract: DDL + bulk inserts that turn the upstream
corpus into ``data/corpus.db`` (FTS5) and ``data/registry.db``. The READ side
(the served queries) lives in ``backend.repositories``; splitting write-from-read
keeps the serving repositories pure read-only. CENTRAL-005 permits raw SQL here.
"""
