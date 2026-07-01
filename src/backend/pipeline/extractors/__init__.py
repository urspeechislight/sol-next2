"""Phase 3 behavior-gated extractors.

Each extractor consumes a span whose behavior segment routed in Phase 2 and
produces Entity/Unit objects from its Phase 2 pattern matches — it never re-scans
span.text. The behavior-to-extractor registry is wired in once the orchestrator
(extract) lands; this package currently holds the hadith narrator extractor.
"""
