"""Tests for the centralization handler + its YAML-driven rule set."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from lib import paths
from lib.context import HookContext
from lib.handlers import centralization


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Point centralization at a temp repo so file globs are deterministic."""
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setattr(paths, "REPO_ROOT", root)
    monkeypatch.setattr(centralization, "REPO_ROOT", root)
    monkeypatch.setattr(
        centralization,
        "POLICY_FILE",
        root / ".claude" / "policies" / "centralization.yaml",
    )
    (root / ".claude/policies").mkdir(parents=True)
    yield root


def _write_policy(repo: Path, body: str) -> None:
    (repo / ".claude/policies/centralization.yaml").write_text(body, encoding="utf-8")


def _ctx(file_path: Path, content: str) -> HookContext:
    return HookContext(
        tool_name="Write",
        file_path=file_path.resolve(),
        command=None,
        new_content=content,
        old_content=None,
    )


def test_should_block_os_getenv_outside_settings(repo: Path) -> None:
    """`os.getenv` may only be called from the settings module."""
    _write_policy(
        repo,
        "version: 1\nrules:\n"
        "  - id: CENTRAL-001-env\n"
        "    description: Env reads only in settings.\n"
        "    kind: ast\n"
        "    ast_match: [os.getenv]\n"
        "    suffixes: [py]\n"
        "    allowed_in: ['src/backend/core/settings.py']\n"
        "    fix: Use Settings.\n",
    )
    target = repo / "src/backend/api/routes.py"
    target.parent.mkdir(parents=True)
    decision = centralization.check(_ctx(target, "import os\nx = os.getenv('FOO')\n"))
    assert decision.severity == "block"
    assert decision.rule_id == "CENTRAL-001-env"


def test_should_allow_os_getenv_in_settings(repo: Path) -> None:
    """The settings module is the one allowed home."""
    _write_policy(
        repo,
        "version: 1\nrules:\n"
        "  - id: CENTRAL-001-env\n"
        "    description: Env reads only in settings.\n"
        "    kind: ast\n"
        "    ast_match: [os.getenv]\n"
        "    suffixes: [py]\n"
        "    allowed_in: ['src/backend/core/settings.py']\n"
        "    fix: Use Settings.\n",
    )
    target = repo / "src/backend/core/settings.py"
    target.parent.mkdir(parents=True)
    decision = centralization.check(_ctx(target, "import os\nx = os.getenv('FOO')\n"))
    assert decision.severity == "allow"


def test_should_block_re_compile_outside_patterns(repo: Path) -> None:
    """Regexes must live in patterns modules."""
    _write_policy(
        repo,
        "version: 1\nrules:\n"
        "  - id: CENTRAL-002-regex\n"
        "    description: Regex only in patterns.\n"
        "    kind: ast\n"
        "    ast_match: [re.compile]\n"
        "    suffixes: [py]\n"
        "    allowed_in: ['src/backend/patterns.py']\n"
        "    fix: Move to patterns.py.\n",
    )
    target = repo / "src/backend/utils/text.py"
    target.parent.mkdir(parents=True)
    decision = centralization.check(_ctx(target, "import re\np = re.compile(r'x')\n"))
    assert decision.severity == "block"


def test_should_block_bare_http_status_code(repo: Path) -> None:
    """`status_code=404` is a magic number disguised."""
    _write_policy(
        repo,
        "version: 1\nrules:\n"
        "  - id: CENTRAL-003-http-status\n"
        "    description: No bare HTTP codes.\n"
        "    kind: regex\n"
        '    pattern: \'\\b(status_code|status)\\s*=\\s*(200|404)\\b\'\n'
        "    suffixes: [py]\n"
        "    allowed_in: ['src/backend/core/http.py']\n"
        "    fix: Use status.HTTP_404_NOT_FOUND.\n",
    )
    target = repo / "src/backend/api/routes.py"
    target.parent.mkdir(parents=True)
    decision = centralization.check(
        _ctx(target, "def fn():\n    return Response(status_code=404)\n")
    )
    assert decision.severity == "block"


def test_should_block_route_decorator_outside_api(repo: Path) -> None:
    """`@router.get(...)` only in routes modules."""
    _write_policy(
        repo,
        "version: 1\nrules:\n"
        "  - id: CENTRAL-004-routes\n"
        "    description: Routes only under api/.\n"
        "    kind: regex\n"
        '    pattern: \'^\\s*@(router|app)\\.(get|post|put|delete)\\s*\\(\'\n'
        "    suffixes: [py]\n"
        "    allowed_in: ['src/backend/api/**/*.py']\n"
        "    fix: Move under api/.\n",
    )
    target = repo / "src/backend/services/handlers.py"
    target.parent.mkdir(parents=True)
    decision = centralization.check(
        _ctx(target, "@router.get('/x')\ndef fn():\n    return None\n")
    )
    assert decision.severity == "block"


def test_should_block_raw_sql_outside_repositories(repo: Path) -> None:
    """SELECT/INSERT strings only in repositories or migrations."""
    _write_policy(
        repo,
        "version: 1\nrules:\n"
        "  - id: CENTRAL-005-sql\n"
        "    description: SQL only in repositories.\n"
        "    kind: regex\n"
        '    pattern: \'["\\x27](?:\\s*--[^\\n]*\\n)?\\s*(SELECT|INSERT\\s+INTO)\\b\'\n'
        "    suffixes: [py]\n"
        "    allowed_in: ['src/backend/repositories/**/*.py']\n"
        "    fix: Move SQL to repositories.\n",
    )
    target = repo / "src/backend/services/books.py"
    target.parent.mkdir(parents=True)
    decision = centralization.check(
        _ctx(target, "SQL = 'SELECT * FROM books'\n")
    )
    assert decision.severity == "block"


def test_should_skip_when_pattern_is_in_comment(repo: Path) -> None:
    """Comments mentioning a forbidden token don't trigger the rule."""
    _write_policy(
        repo,
        "version: 1\nrules:\n"
        "  - id: CENTRAL-005-sql\n"
        "    description: SQL only in repositories.\n"
        "    kind: regex\n"
        '    pattern: \'["\\x27](?:\\s*--[^\\n]*\\n)?\\s*(SELECT|INSERT\\s+INTO)\\b\'\n'
        "    suffixes: [py]\n"
        "    allowed_in: ['src/backend/repositories/**/*.py']\n"
        "    fix: Move SQL to repositories.\n",
    )
    target = repo / "src/backend/services/books.py"
    target.parent.mkdir(parents=True)
    decision = centralization.check(
        _ctx(target, "# This service runs SELECT internally via the repo layer.\nx = 1\n")
    )
    assert decision.severity == "allow"


def test_should_allow_when_no_policy_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Handler is a no-op when centralization.yaml is missing."""
    monkeypatch.setattr(centralization, "POLICY_FILE", tmp_path / "missing.yaml")
    target = tmp_path / "x.py"
    decision = centralization.check(_ctx(target, "import os\nx = os.getenv('FOO')\n"))
    assert decision.severity == "allow"


def test_should_skip_when_pattern_is_in_js_line_comment(repo: Path) -> None:
    """`// fetch(...)` in a JS comment must not trigger the api-client rule."""
    _write_policy(
        repo,
        "version: 1\nrules:\n"
        "  - id: CENTRAL-007-frontend-api\n"
        "    description: API only via shared client.\n"
        "    kind: regex\n"
        '    pattern: \'\\bfetch\\s*\\(\'\n'
        "    suffixes: [tsx]\n"
        "    allowed_in: ['frontend/src/lib/api/**/*']\n"
        "    fix: Use api client.\n",
    )
    target = repo / "frontend/src/components/Foo.tsx"
    target.parent.mkdir(parents=True)
    decision = centralization.check(
        _ctx(target, "// TODO: replace fetch( call with api client\nconst x = 1;\n")
    )
    assert decision.severity == "allow"


def test_should_skip_when_pattern_is_in_js_block_comment(repo: Path) -> None:
    """`/* ... fetch( ... */` block comment must not trigger the rule."""
    _write_policy(
        repo,
        "version: 1\nrules:\n"
        "  - id: CENTRAL-007-frontend-api\n"
        "    description: API only via shared client.\n"
        "    kind: regex\n"
        '    pattern: \'\\bfetch\\s*\\(\'\n'
        "    suffixes: [tsx]\n"
        "    allowed_in: ['frontend/src/lib/api/**/*']\n"
        "    fix: Use api client.\n",
    )
    target = repo / "frontend/src/components/Foo.tsx"
    target.parent.mkdir(parents=True)
    body = "/* The old version called fetch( directly — replaced with api. */\nconst x = 1;\n"
    decision = centralization.check(_ctx(target, body))
    assert decision.severity == "allow"


def test_should_block_raw_fetch_in_tsx(repo: Path) -> None:
    """A real `fetch(` call in TSX outside the api/ layer is blocked."""
    _write_policy(
        repo,
        "version: 1\nrules:\n"
        "  - id: CENTRAL-007-frontend-api\n"
        "    description: API only via shared client.\n"
        "    kind: regex\n"
        '    pattern: \'\\bfetch\\s*\\(\'\n'
        "    suffixes: [tsx]\n"
        "    allowed_in: ['frontend/src/lib/api/**/*']\n"
        "    fix: Use api client.\n",
    )
    target = repo / "frontend/src/components/Foo.tsx"
    target.parent.mkdir(parents=True)
    decision = centralization.check(
        _ctx(target, "export function Foo() {\n  return fetch('/api/x').then(r => r.json());\n}\n")
    )
    assert decision.severity == "block"


def test_should_block_jwt_encode_outside_auth(repo: Path) -> None:
    """jwt.encode outside src/backend/auth/ is blocked."""
    _write_policy(
        repo,
        "version: 1\nrules:\n"
        "  - id: CENTRAL-009-jwt\n"
        "    description: JWT only in auth.\n"
        "    kind: ast\n"
        "    ast_match: [jwt.encode, jwt.decode]\n"
        "    suffixes: [py]\n"
        "    allowed_in: ['src/backend/auth/**/*.py']\n"
        "    fix: Move to auth module.\n",
    )
    target = repo / "src/backend/services/login.py"
    target.parent.mkdir(parents=True)
    decision = centralization.check(_ctx(target, "import jwt\nt = jwt.encode({}, 'k')\n"))
    assert decision.severity == "block"


def test_should_allow_jwt_encode_inside_auth(repo: Path) -> None:
    """jwt.encode inside src/backend/auth/ is allowed."""
    _write_policy(
        repo,
        "version: 1\nrules:\n"
        "  - id: CENTRAL-009-jwt\n"
        "    description: JWT only in auth.\n"
        "    kind: ast\n"
        "    ast_match: [jwt.encode, jwt.decode]\n"
        "    suffixes: [py]\n"
        "    allowed_in: ['src/backend/auth/**/*.py']\n"
        "    fix: Move to auth module.\n",
    )
    target = repo / "src/backend/auth/tokens.py"
    target.parent.mkdir(parents=True)
    decision = centralization.check(_ctx(target, "import jwt\nt = jwt.encode({}, 'k')\n"))
    assert decision.severity == "allow"


def test_should_block_uuid_uuid4_outside_ids(repo: Path) -> None:
    """uuid.uuid4 outside the ids module is blocked."""
    _write_policy(
        repo,
        "version: 1\nrules:\n"
        "  - id: CENTRAL-015-ids\n"
        "    description: IDs only via core/ids.py.\n"
        "    kind: ast\n"
        "    ast_match: [uuid.uuid4]\n"
        "    suffixes: [py]\n"
        "    allowed_in: ['src/backend/core/ids.py']\n"
        "    fix: Move to ids.\n",
    )
    target = repo / "src/backend/services/books.py"
    target.parent.mkdir(parents=True)
    decision = centralization.check(_ctx(target, "import uuid\nid = uuid.uuid4()\n"))
    assert decision.severity == "block"
