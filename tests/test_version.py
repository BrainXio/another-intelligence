"""Test that the package version is exposed correctly."""

import another_intelligence


def test_version_is_string():
    """Version must be a semantic version string."""
    assert isinstance(another_intelligence.__version__, str)


def test_version_is_semantic():
    """Version must follow MAJOR.MINOR.PATCH format."""
    parts = another_intelligence.__version__.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_version_matches_pyproject():
    """Version in __init__ must match pyproject.toml."""
    assert another_intelligence.__version__ == "0.1.0"
