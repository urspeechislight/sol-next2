#!/usr/bin/env bash
# Headless code review via `claude -p` (Claude Code non-interactive mode).
#
# Sends a diff to Claude Code in headless mode and gates on the verdict:
# exit 0 = clean or the reviewer could not be reached, exit 1 = blockers found.
# Wire into CI or a pre-push hook as a second-opinion gate that complements
# the deterministic lefthook harness (this one catches judgement-level issues
# the rule handlers can't encode). It is advisory: when the reviewer is
# unavailable it steps aside loudly rather than blocking the push, the same
# stance lefthook takes when the claude CLI is not installed.
#
# Usage:
#   scripts/cca_review.sh            # review staged changes
#   scripts/cca_review.sh --push     # review the commits this push adds
set -euo pipefail

mode="${1:-}"

if ! command -v claude >/dev/null 2>&1; then
  echo "cca_review: 'claude' CLI not found on PATH — install Claude Code to run headless review." >&2
  exit 2
fi

if [[ "$mode" == "--push" ]]; then
  # A pre-push review must look at exactly what the push adds: the commits on
  # this branch that its remote-tracking ref does not have yet. Diffing against
  # an integration branch such as main re-reads the entire repository whenever
  # main has not received this work, which swamps the reviewer and stalls the
  # push. Before the branch exists on the remote there is no delta to review.
  if ! git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' >/dev/null 2>&1; then
    echo "cca_review: no upstream for this branch yet (first push) — nothing to review."
    exit 0
  fi
  diff="$(git diff '@{upstream}..HEAD')"
else
  diff="$(git diff --staged)"
fi

# The emptiness check must never be a bash pattern substitution over the
# whole diff: ${diff//...} rewrites the string in-process and goes
# quadratic on multi-megabyte deltas (a 69-commit push pinned bash at 100%
# CPU for 19+ minutes, upstream of the claude timeout guard). grep does the
# same check in C time.
if ! grep -q '[^[:space:]]' <<<"$diff"; then
  echo "cca_review: empty diff — nothing to review."
  exit 0
fi

# A delta beyond what a reviewer can usefully read gets skipped loudly, the
# same step-aside stance as an unreachable reviewer. This also bounds every
# later bash operation on the string.
max_diff_bytes=500000
if (( ${#diff} > max_diff_bytes )); then
  echo "cca_review: delta is ${#diff} bytes (cap ${max_diff_bytes}) — too large for a useful headless review, not blocking." >&2
  exit 0
fi

read -r -d '' prompt <<'PROMPT' || true
You are reviewing a diff for the sol-next2 repo. Its rules live in CLAUDE.md:
no silent fallbacks, fail loud, wrong-is-worse-than-absent, design-token SSOT,
centralization (env/regex/status/routes), backend must not import frontend, and
durability (no patchwork).
Review ONLY the diff below for violations of those principles and for plain
correctness bugs. Ignore style the lefthook harness already enforces.
Fail the diff for these durability violations, which the deterministic harness
cannot catch:
- Reactive blocklist: a set/list/dict of domain strings extended with more bad
  examples instead of a structural rule (for example, adding stray words to a
  name-cleaning lookup rather than parsing by grammar). A hand-maintained lookup
  is acceptable only when it is a genuinely closed linguistic class, and the
  diff should say why it is closed.
- Symptom-masking change: it suppresses a symptom while leaving the root cause,
  adds a second parallel code path where the old one should have been deleted,
  or would need a "for now" to justify it.
- Dead code: a function, constant, or branch the diff adds or leaves in place
  that nothing calls.
- Reinvention: a formatter, component, store, parser, validator, vocabulary or
  label map, type, or constant built from scratch when an equivalent already
  exists in the repo. Reuse or extend the canonical module instead of forking a
  second copy. Check the usual homes named in CLAUDE.md's capabilities map
  (lib/utils, lib/design-system, lib/constants, lib/types, core/constants,
  build/name_registry, build/mizan_names). Reusing what exists keeps the project
  unified; a parallel implementation is a durability failure even when it works.
Respond with a single line of JSON and nothing else:
{"verdict":"pass"|"fail","blockers":["..."],"notes":["..."]}
PROMPT

# --print = headless text output; the model returns its final answer (the
# one-line verdict JSON the prompt asks for). Bounded tools so the reviewer
# reads but never edits. A hard timeout keeps a stuck or unreachable request
# from hanging the push.
review_timeout_seconds=240
set +e
result="$(printf '%s\n\n--- DIFF ---\n%s\n' "$prompt" "$diff" \
  | timeout "${review_timeout_seconds}" claude -p --allowedTools "Read" "Grep")"
claude_status=$?
set -e
if [[ "$claude_status" -eq 124 ]]; then
  echo "cca_review: claude -p exceeded ${review_timeout_seconds}s — reviewer unreachable, not blocking the push." >&2
  exit 0
fi
if [[ "$claude_status" -ne 0 ]]; then
  echo "cca_review: claude -p could not run (exit ${claude_status}) — reviewer unreachable, not blocking the push." >&2
  exit 0
fi

echo "$result"

# Extract the verdict from the reviewer's JSON. A response with no parseable
# JSON object means the reviewer gave no usable answer, so step aside loudly
# rather than block the push on a malformed second opinion.
verdict="$(python3 -c '
import sys, json, re
match = re.search(r"\{.*\}", sys.argv[1], re.DOTALL)
if not match:
    print("unparseable"); raise SystemExit(0)
try:
    print(json.loads(match.group(0)).get("verdict", "fail"))
except json.JSONDecodeError:
    print("unparseable")
' "$result")"

if [[ "$verdict" == "pass" ]]; then
  echo "cca_review: PASS"
  exit 0
fi
if [[ "$verdict" == "unparseable" ]]; then
  echo "cca_review: reviewer returned no parseable verdict — not blocking the push." >&2
  exit 0
fi
echo "cca_review: FAIL — see blockers above." >&2
exit 1
