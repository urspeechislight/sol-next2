<!-- GENERATED from .claude/policies/quality.yaml and the handler DOC anchors by .claude/lib/gen_standards_docs.py. Do not edit by hand; run `pnpm docs:standards`. -->

# Quality Standards

Enforced by the harness; see the named handler under `.claude/lib/handlers/` for
the exact check.

<a id="bash-file-writes"></a>

## Bash File Writes

- **BASH-100** (`bash_file_write`, block) — Block Bash commands that write
  project files, bypassing the Write hook.

<a id="code-quality"></a>

## Code Quality

- **PY-001** (`typed_python`, block) — Public Python functions need return-type
  annotations.
- **QUAL-012** (`no_silent_except`, block) — No bare `except:` or
  `except: pass`.
- **QUAL-013** (`no_print`, block) — print() is blocked in production Python
  (src/backend, src/pipeline); log via structlog. scripts/, tests/, .claude/,
  and **main** modules are exempt. _print bypasses the structured-logging
  contract — no level, no context, invisible to log shipping._
- **QUAL-014** (`magic_numbers`, advisory) — Magic numeric literals in
  production Python code.
- **QUAL-020** (`post_ruff`, block) — PostToolUse: run ruff against the
  just-written Python file.

<a id="comments"></a>

## Comments

- **DOC-011** (`no_inline_comments`, block) — Code comments, both inline and
  standalone, are blocked; intent belongs in docstrings and names. Tooling
  directives (# type:, # noqa, ...), the shebang, section dividers, and
  unicode-escape annotation lines are exempt. _Comments drift out of sync with
  the code they describe; docstrings and names do not._

<a id="destructive-commands"></a>

## Destructive Commands

- **DANGEROUS_BASH** (`dangerous_bash`, block) — PreToolUse:Bash — block
  obviously dangerous shell commands.

<a id="docstrings"></a>

## Docstrings

- **DOC-010** (`docstring_required`, block) — Every public function and class
  needs a docstring. tests/ and **init**.py are skipped; @overload stubs are
  exempt. _The public surface documents intent at the point of use._

<a id="fail-fast"></a>

## Fail Fast

- **FAILFAST-001** (`fail_loud`, block) — Silent fallbacks inside `except`
  blocked: `return None|[]|{}|"UNKNOWN"`, bare `continue`, or `pass`-only body —
  unless logging / raise precedes. _"Wrong is worse than absent." A swallowed
  exception that returns None looks identical to a normal-empty None. The caller
  must be able to tell a failure from data._
- **FAILFAST-002** (`no_fallback`, block) — The strict sibling of fail*loud: the
  word `fallback` / `fall back`, a Python `except` with no `raise`, and a JS/TS
  `catch` with no `throw` are blocked in src/ and scripts/. \_fail_loud permits
  "log then return None"; no_fallback rejects any error-recovery that lets the
  program continue without telling the caller something failed. Absence must be
  modelled explicitly, not synthesised in a handler.*

<a id="helper-functions"></a>

## Helper Functions

- **FUNC-001** (`helper_constraints`, block) — Function names must say what they
  do: vague names (helper, process, handle), multi-responsibility names (_and_ /
  _then_ / _or_), and names longer than 40 characters are blocked. _A name that
  hides the responsibility, or bundles several, is a single-responsibility
  smell._
- **FUNC-002** (`helper_constraints`, advisory) — More than 5 parameters
  (excluding self / cls) is an advisory design smell, not a block.
  _Hard-blocking the count manufactured transfer dataclasses whose only job was
  to smuggle the same arguments past the gate, which is worse than a wide
  signature; the author must weigh it instead._

<a id="imports--boundaries"></a>

## Imports & Boundaries

- **BND-001** (`import_boundaries`, block) — $lib/design-system/internal is
  private. _Encapsulation — only the design system itself uses internal/._
- **BND-002** (`import_boundaries`, block) — Frontend may not import backend /
  pipeline Python packages. _Frontend talks to backend over HTTP, not
  in-process._

<a id="no-patchwork"></a>

## No Patchwork

- **PATCH-001** (`no_patchwork`, block) — Self-admitted patchwork vocabulary in
  src/ and frontend/src/ is blocked: band-aid, stopgap, kludge, duct-tape,
  patchwork, patch-job, quick-fix, quick-and-dirty, hacky, "good enough for
  now". _A word that admits a corner-cut names a non-durable fix. Resolve the
  root cause and delete what it replaces; when filtering domain data, encode the
  structural or grammatical rule that decides membership, never an enumeration
  of bad examples grown one bug at a time. This is the mechanical floor: the
  push-time AI review (scripts/cca_review.sh) and the CLAUDE.md durability
  directive catch the reactive-blocklist form a regex cannot._

<a id="security"></a>

## Security

- **SEC-001** (`secret_scanner`, block) — High-confidence secret patterns
  blocked at write time.
- **SEC-002** (`sensitive_read`, block) — Audit reads of sensitive files; block
  reads of obvious secret stores.
- **SEC-004** (`web_access`, block) — Log every external fetch; block known
  data-exfil-shaped destinations.

<a id="size-caps"></a>

## Size Caps

- **QUAL-010** (`file_size_cap`, advisory) — File LOC signal at 400, advisory
  only. A large file calls for extracting a real concept, never a mechanical
  split into facade plus shards.
- **QUAL-011** (`function_size_cap`, advisory) — Function LOC signal at 80,
  advisory only. A long function calls for a named extraction, never carving at
  an arbitrary line.

<a id="ssot-dry"></a>

## SSOT DRY

- **BUILD-001** (`single_pyproject`, block) — pyproject.toml / package.json /
  lockfiles live at the repo root only; Docker files at root or under deploy/.
  _Two manifests split the dep graph — upgrades to one don't reach the other and
  behaviours drift._
- **CENTRAL-001-env** (`centralization`, block) — os.getenv / os.environ reads
  only in settings modules.
- **CENTRAL-002-regex** (`centralization`, block) — re.compile / re.search /
  etc. only in patterns modules.
- **CENTRAL-003-http-status** (`centralization`, block) — HTTP status codes must
  be named, not bare integers.
- **CENTRAL-004-routes** (`centralization`, block) — HTTP route decorators only
  in src/backend/api/ modules.
- **CENTRAL-005-sql** (`centralization`, block) — Raw SQL strings only in
  repositories / migrations.
- **DRY-001** (`function_duplication`, block) — Public module-level functions
  are defined in exactly one file under src/. Re-defining the same name
  elsewhere is blocked. _Two `normalize_arabic` in two modules drift; callers
  pick one or the other and the behaviours diverge._
- **DRY-002** (`class_duplication`, block) — Public module-level classes are
  defined in exactly one file under src/. Covers DTOs, schemas, enums,
  exceptions, TypedDict, NamedTuple. _Two `Book` Pydantic models in two modules
  diverge silently; two `ValidationError` exceptions catch each other's
  instances by accident._
- **SSOT-001** (`constant_sprawl`, block) — Module-level constants live in
  exactly one file. Name re-declarations, value re-aliasing, and a re-enumerated
  string vocabulary (4+ members, seen through a helper wrapper like
  _norm_set/frozenset and past a private name) across files are all blocked.
  _"If a constant doesn't exist is the only time you can create one." TIMEOUT=30
  in two modules diverges silently when one gets re-tuned. The same Arabic
  particle set typed in two files (authority._LINKS vs name_registry.LINKS) is
  the same divergence risk, so the string-set check catches derived, private
  duplicates the literal check cannot see._

<a id="tests"></a>

## Tests

- **TEST-001** (`test_naming`, block) — Test names follow
  test*should*<verb>_<object>_<condition>.

<a id="ui-centralization"></a>

## UI Centralization

- **UI-001** (`css_duplication`, block) — An identical CSS selector body defined
  in two files under frontend/src is blocked; each selector is defined once.
  _One CSS file per primitive/component; a selector copied into two files drifts
  silently._
