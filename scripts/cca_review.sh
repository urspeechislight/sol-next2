#!/usr/bin/env bash
# Headless code review via `claude -p` (Claude Code non-interactive mode).
#
# Sends a diff to Claude Code in headless mode and gates on the verdict:
# exit 0 = clean, exit 1 = blockers found, exit 2 = could not run.
# Wire into CI or a pre-push hook as a second-opinion gate that complements
# the deterministic lefthook harness (this one catches judgement-level issues
# the rule handlers can't encode).
#
# Usage:
#   scripts/cca_review.sh            # review staged changes
#   scripts/cca_review.sh main       # review current branch vs origin/main
set -euo pipefail

base="${1:-}"

if ! command -v claude >/dev/null 2>&1; then
  echo "cca_review: 'claude' CLI not found on PATH — install Claude Code to run headless review." >&2
  exit 2
fi

if [[ -n "$base" ]]; then
  diff="$(git diff "origin/${base}...HEAD")"
else
  diff="$(git diff --staged)"
fi

if [[ -z "${diff//[$' \t\r\n']/}" ]]; then
  echo "cca_review: empty diff — nothing to review."
  exit 0
fi

read -r -d '' prompt <<'PROMPT' || true
You are reviewing a diff for the sol-next2 repo. Its rules live in CLAUDE.md:
no silent fallbacks, fail loud, wrong-is-worse-than-absent, design-token SSOT,
centralization (env/regex/status/routes), backend must not import frontend.
Review ONLY the diff below for violations of those principles and for plain
correctness bugs. Ignore style the lefthook harness already enforces.
Respond with a single line of JSON and nothing else:
{"verdict":"pass"|"fail","blockers":["..."],"notes":["..."]}
PROMPT

# --print = headless; bounded tools so the reviewer reads but never edits.
result="$(printf "%s\n\n--- DIFF ---\n%s\n" "$prompt" "$diff" \
  | claude -p --output-format json --allowedTools "Read" "Grep")"

# --output-format json wraps the model text in a {"result": "..."} envelope.
verdict_line="$(printf "%s" "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get(\"result\",\"\"))")"
echo "$verdict_line"

verdict="$(printf "%s" "$verdict_line" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get(\"verdict\",\"fail\"))")"
if [[ "$verdict" == "pass" ]]; then
  echo "cca_review: PASS"
  exit 0
fi
echo "cca_review: FAIL — see blockers above." >&2
exit 1
