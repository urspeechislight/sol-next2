"""Ported sol-next NLP pipeline (phases 2-3: segment + extract).

Vendored from the sibling sol-next project and adapted to sol-next2's harness
rules: comment-free source, approved-domain constants, single compile path for
regexes (backend.patterns), and a config loaded from config/sol.yaml.

Phase 1 (ingest) is intentionally NOT ported: sol-next2 already produces page
rows via backend.repositories.reader.page_rows, which feed segment directly.
Phase 4 (enrich) and Phase 5 (graph) remain stubs upstream and are out of scope
for this port.
"""
