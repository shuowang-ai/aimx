from __future__ import annotations

from pathlib import Path

import pytest

from aimx.commands.query import QueryInvocation, normalize_repo_path


def test_normalize_repo_path_keeps_repo_root() -> None:
    normalized = normalize_repo_path(Path("data"))

    assert normalized == Path("data")


def test_normalize_repo_path_converts_dot_aim_directory_to_parent() -> None:
    normalized = normalize_repo_path(Path("data/.aim"))

    assert normalized == Path("data")


def test_normalize_repo_path_rejects_missing_path() -> None:
    with pytest.raises(ValueError, match="does not exist"):
        normalize_repo_path(Path("missing-repo"))


def test_query_invocation_rejects_unsupported_target() -> None:
    with pytest.raises(ValueError, match="Unsupported query target"):
        QueryInvocation(
            target="artifacts",
            expression="metric.name == 'loss'",
            repo_path=Path("data"),
            output_json=False,
        )

