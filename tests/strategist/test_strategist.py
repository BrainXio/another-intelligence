"""Tests for the Strategist (PFC) brain region."""

import pytest

from another_intelligence.strategist import Proposal, Strategist


class TestProposal:
    """Proposal dataclass validation."""

    def test_basic_construction(self):
        p = Proposal(options=["a", "b"], expected_values=[0.5, 0.6])
        assert p.options == ["a", "b"]
        assert p.expected_values == [0.5, 0.6]

    def test_mismatched_lengths_raise(self):
        with pytest.raises(ValueError, match="same length"):
            Proposal(options=["a", "b"], expected_values=[0.5])


class TestStrategistInit:
    """Construction and configuration."""

    def test_default_base_value(self):
        s = Strategist()
        assert s._base_value == 0.5

    def test_custom_base_value(self):
        s = Strategist(base_value=1.0)
        assert s._base_value == 1.0


class TestStrategistPropose:
    """Option proposal and expected value computation."""

    def test_returns_proposal(self):
        s = Strategist()
        result = s.propose("What should I do?")
        assert isinstance(result, Proposal)

    def test_default_options(self):
        s = Strategist()
        result = s.propose("test")
        assert result.options == ["proceed", "wait", "abort"]

    def test_custom_options(self):
        s = Strategist()
        result = s.propose("test", options=["x", "y"])
        assert result.options == ["x", "y"]

    def test_expected_values_length_matches_options(self):
        s = Strategist()
        result = s.propose("test", options=["a", "b", "c"])
        assert len(result.expected_values) == 3

    def test_expected_values_use_base_value(self):
        s = Strategist(base_value=0.5)
        result = s.propose("test")
        assert all(v == 0.5 for v in result.expected_values)

    def test_expected_values_include_memory(self):
        s = Strategist(base_value=0.5)
        result = s.propose("test", memory={"proceed": 0.2})
        idx = result.options.index("proceed")
        assert result.expected_values[idx] == 0.7

    def test_query_is_stored(self):
        s = Strategist()
        result = s.propose("build a bridge")
        assert result.query == "build a bridge"


class TestStrategistExpectedValue:
    """Single-option expected value helper."""

    def test_no_memory(self):
        s = Strategist(base_value=0.5)
        assert s.expected_value("foo") == 0.5

    def test_with_memory(self):
        s = Strategist(base_value=0.5)
        assert s.expected_value("foo", memory={"foo": 0.3}) == 0.8

    def test_memory_missing_key(self):
        s = Strategist(base_value=0.5)
        assert s.expected_value("foo", memory={"bar": 0.3}) == 0.5


class TestStrategistIngestPrototypes:
    def test_ranks_by_expected_value(self) -> None:
        s = Strategist(base_value=0.5)
        shortlist = [
            {"name": "alpha", "description": "First"},
            {"name": "beta", "description": "Second"},
            {"name": "gamma", "description": "Third"},
        ]
        ranked = s.ingest_prototypes(
            shortlist,
            memory={"beta": 0.3, "gamma": 0.1},
        )
        assert len(ranked) == 3
        assert ranked[0]["name"] == "beta"
        assert ranked[1]["name"] == "gamma"
        assert ranked[2]["name"] == "alpha"

    def test_respects_top_n(self) -> None:
        s = Strategist()
        shortlist = [{"name": f"item_{i}", "description": f"Desc {i}"} for i in range(10)]
        ranked = s.ingest_prototypes(shortlist, top_n=3)
        assert len(ranked) == 3

    def test_includes_rationale_and_deps(self) -> None:
        s = Strategist()
        shortlist = [
            {
                "name": "feat_x",
                "description": "A feature",
                "dependencies": ["feat_y"],
            }
        ]
        ranked = s.ingest_prototypes(shortlist)
        assert len(ranked) == 1
        assert "rationale" in ranked[0]
        assert ranked[0]["dependencies"] == ["feat_y"]

    def test_empty_shortlist(self) -> None:
        s = Strategist()
        ranked = s.ingest_prototypes([], top_n=5)
        assert ranked == []
