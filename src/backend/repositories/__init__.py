"""Data-access layer. All persistence (SQL/files/etc.) lives here.

Service / API layers call repositories; they never reach past this layer
to the storage backend.
"""
