"""Pin the harness workspace-glob stub to the real pnpm-workspace.yaml.

``paths.STUB_WORKSPACE_GLOBS`` is what the laptop-side ssh_remote_write
validator uses, because the laptop stub has no ``pnpm-workspace.yaml``. On
buildhost the manifest exists and ``workspace_globs()`` reads it, so assert the
mirrored stub equals it: the two cannot drift without this test going red.
"""

from __future__ import annotations

from lib import paths


def test_should_match_declared_packages_when_manifest_present() -> None:
    """The mirrored stub list must equal the manifest's packages on buildhost."""
    manifest = paths.REPO_ROOT / "pnpm-workspace.yaml"
    if not manifest.exists():
        assert paths.workspace_globs() == paths.STUB_WORKSPACE_GLOBS
        return
    assert set(paths.STUB_WORKSPACE_GLOBS) == set(paths.workspace_globs())


def test_should_recognize_frontend_as_workspace_package() -> None:
    """`frontend` must resolve as a workspace package dir (the migration target)."""
    assert paths.is_declared_package_dir("frontend")
