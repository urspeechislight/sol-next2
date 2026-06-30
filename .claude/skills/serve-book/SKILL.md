---
name: serve-book
description: >-
  Preview ONE book from the corpus in sol-next2's single-book demo runner
  (buildhost port 8766). Use when the user asks to "preview", "demo", "open", or
  "look at" a specific book by slug/URN before it ships. Not for the full
  catalog — that is the main frontend on :8765.
allowed-tools: Bash(ssh:*), Bash(curl:*), Read
---

# Serve a single book (demo runner)

The demo runner is `scripts/serve` on buildhost, listening on **:8766**. It
renders exactly one book, chosen by the `SOL_DEMO_BOOK` environment variable (a
book slug/URN). This skill (re)points it at a book and confirms it renders.

> Tools are restricted (`allowed-tools`) to ssh + curl + Read: this skill
> inspects and restarts a known process, it must never edit source.

## Steps

1. **Resolve the book.** Confirm the slug exists in the catalog (fail loud if
   not — do not silently pick a default):

   ```bash
   curl -s "http://buildhost:8001/api/books/<urn>" | head -c 400
   ```

   A 404 means the slug is wrong — stop and report it; do not guess another.

2. **Point the runner at it and restart** (only the `scripts/serve` process on
   :8766 — never touch :8001/:8765):

   ```bash
   ssh -i ~/.ssh/buildhost_key dev@buildhost "pkill -f scripts/serve || true; \
     cd ~/code/sol-next2 && SOL_DEMO_BOOK=<urn> \
     nohup python3 scripts/serve > /tmp/sol-next2-demo.log 2>&1 & disown"
   ```

3. **Verify it came up** before claiming success:

   ```bash
   sleep 1; curl -sf "http://buildhost:8766/" >/dev/null && echo "demo up" \
     || { echo "demo failed — see /tmp/sol-next2-demo.log"; exit 1; }
   ```

4. Tell the user the preview URL: `http://buildhost:8766` (also reachable at
   `http://10.0.0.10:8766`). If a new host is used, the backend CORS list in
   buildhost's `.env` must include it (see CLAUDE.md).

## Guardrails

- One book at a time — this is a focused previewer, not the catalog.
- If the runner won't start, surface the log tail; never report success blind.
