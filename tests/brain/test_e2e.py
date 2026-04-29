"""End-to-end tests for the DigitalBrain PPAC loop across diverse prompts.

These tests validate that the 5-stage strict serial pipeline (Strategist →
Executor → Reflex → Outcome → Learning) executes cleanly on realistic inputs
and that every stage emits the expected events.
"""

from __future__ import annotations

from typing import Any

import pytest

from another_intelligence.brain import DigitalBrain
from another_intelligence.events import BrainRegionActivated, RPEUpdated

PROMPT_CASES: list[tuple[str, list[str] | None]] = [
    # 1. Simple factual query
    ("What is the capital of France?", None),
    # 2. Boolean / choice question
    ("Should I enable debug logging?", ["yes", "no"]),
    # 3. Multi-step planning
    (
        "Plan a 3-step migration from SQLite to PostgreSQL including backups.",
        None,
    ),
    # 4. Tool-using task (select a tool)
    (
        "I need to read a config file. Which tool should I use?",
        ["read_file", "write_file", "list_directory", "grep_search"],
    ),
    # 5. Creative / open-ended
    (
        "Generate a creative name for a neuroscience-themed CLI tool.",
        None,
    ),
    # 6. Error handling / recovery
    (
        "The build is failing with a lint error. What's the best next action?",
        ["fix lint and rebuild", "skip lint and rebuild", "investigate error"],
    ),
    # 7. Resource-constrained decision
    (
        "We have 1GB RAM free and need to start a new service.",
        ["start immediately", "free memory first", "delay start"],
    ),
    # 8. Comparative evaluation
    (
        "Compare React and Vue for a small dashboard project.",
        None,
    ),
    # 9. Safety / permission-sensitive
    (
        "Should I grant 'filesystem.write' to an untrusted MCP server?",
        ["grant", "deny", "ask user"],
    ),
    # 10. Ambiguous / underspecified
    (
        "What should I do next?",
        None,
    ),
]


class TestDecideDiversePrompts:
    """Parameterized end-to-end decide() across 10 prompt categories."""

    @pytest.mark.parametrize("query,options", PROMPT_CASES)
    def test_decide_completes_without_exception(self, query: str, options: list[str] | None):
        brain = DigitalBrain()
        result = brain.decide(query=query, options=options)
        assert isinstance(result, dict)
        assert "chosen_action" in result
        assert "options" in result
        assert result["chosen_action"] in result["options"]

    @pytest.mark.parametrize("query,options", PROMPT_CASES)
    def test_decide_emits_all_regions(self, query: str, options: list[str] | None):
        brain = DigitalBrain()
        brain.decide(query=query, options=options)
        regions = [e.region for e in brain.events if isinstance(e, BrainRegionActivated)]
        assert "strategist" in regions
        assert "executor" in regions
        assert "reflex" in regions
        assert "learning" in regions

    @pytest.mark.parametrize("query,options", PROMPT_CASES)
    def test_decide_emits_rpe(self, query: str, options: list[str] | None):
        brain = DigitalBrain()
        brain.decide(query=query, options=options)
        rpes = [e for e in brain.events if isinstance(e, RPEUpdated)]
        assert len(rpes) >= 1

    @pytest.mark.parametrize("query,options", PROMPT_CASES)
    def test_regions_fire_in_strict_order(self, query: str, options: list[str] | None):
        brain = DigitalBrain()
        brain.decide(query=query, options=options)
        regions = [e.region for e in brain.events if isinstance(e, BrainRegionActivated)]
        strategist_idx = regions.index("strategist")
        executor_idx = regions.index("executor")
        reflex_idx = regions.index("reflex")
        learning_idx = regions.index("learning")
        assert strategist_idx < executor_idx < reflex_idx < learning_idx

    @pytest.mark.parametrize("query,options", PROMPT_CASES)
    def test_decision_context_key_is_consistent(self, query: str, options: list[str] | None):
        """The chosen action must be a valid option key for memory lookup."""
        brain = DigitalBrain()
        result = brain.decide(query=query, options=options)
        chosen = result["chosen_action"]
        assert chosen in result["options"]
        # Memory is updated with the chosen action as key
        assert chosen in brain.memory or len(brain.memory) > 0

    @pytest.mark.parametrize("query,options", PROMPT_CASES)
    def test_state_returns_to_idle(self, query: str, options: list[str] | None):
        brain = DigitalBrain()
        brain.decide(query=query, options=options)
        from another_intelligence.state import ActivityPhase

        assert brain.state.current == ActivityPhase.IDLE


class TestMultiTurnConversation:
    """Minimum 5-turn conversation with carryover context and memory."""

    TURNS: list[tuple[str, list[str] | None]] = [
        ("Start a new session.", ["proceed", "wait", "abort"]),
        ("List active regions.", None),
        ("What was my first query?", None),
        ("Enable verbose logging.", ["yes", "no"]),
        ("End session and flush state.", ["flush", "keep"]),
    ]

    def test_five_turns_complete(self):
        brain = DigitalBrain()
        decisions: list[dict[str, Any]] = []
        for query, options in self.TURNS:
            result = brain.decide(query=query, options=options)
            decisions.append(result)
        assert len(decisions) == 5

    def test_context_grows_across_turns(self):
        brain = DigitalBrain()
        tokens_before = brain.context.total_tokens
        for query, options in self.TURNS:
            brain.decide(query=query, options=options)
        assert brain.context.total_tokens > tokens_before

    def test_memory_accumulates_across_turns(self):
        brain = DigitalBrain()
        for query, options in self.TURNS:
            brain.decide(query=query, options=options)
        assert len(brain.memory) >= 1

    def test_each_turn_emits_all_regions(self):
        brain = DigitalBrain()
        for query, options in self.TURNS:
            brain.decide(query=query, options=options)
        regions = [e.region for e in brain.events if isinstance(e, BrainRegionActivated)]
        # 5 turns × 4 regions = 20 minimum
        assert regions.count("strategist") == 5
        assert regions.count("executor") == 5
        assert regions.count("reflex") == 5
        assert regions.count("learning") == 5

    def test_events_are_ordered_by_turn(self):
        brain = DigitalBrain()
        for query, options in self.TURNS:
            brain.decide(query=query, options=options)
        events = [e for e in brain.events if isinstance(e, BrainRegionActivated)]
        # Every 4th event should be strategist, in order
        for i in range(5):
            assert events[i * 4].region == "strategist"


class TestRecordOutcomeLoop:
    """Closing the RPE loop with real external outcomes."""

    def test_record_outcome_after_decide(self):
        brain = DigitalBrain()
        result = brain.decide(query="Choose a deployment strategy.")
        decision_id = result["decision_id"]

        # Simulate external feedback (CI passed → positive outcome)
        brain.record_outcome(decision_id=decision_id, expected=0.5, actual=1.0)

        rpes = [e for e in brain.events if isinstance(e, RPEUpdated)]
        assert len(rpes) == 2  # one from decide(), one from record_outcome()
        assert rpes[-1].rpe == 0.5  # actual - expected

    def test_record_outcome_with_negative_feedback(self):
        brain = DigitalBrain()
        result = brain.decide(query="Pick a library.")
        decision_id = result["decision_id"]

        # Simulate external feedback (CI failed → negative outcome)
        brain.record_outcome(decision_id=decision_id, expected=0.8, actual=0.2)

        rpes = [e for e in brain.events if isinstance(e, RPEUpdated)]
        assert rpes[-1].rpe == pytest.approx(-0.6)

    def test_context_key_matches_decision(self):
        brain = DigitalBrain()
        result = brain.decide(query="Select a database.", options=["postgres", "sqlite"])
        decision_id = result["decision_id"]
        chosen = result["chosen_action"]

        # After decide, memory should contain the chosen action
        assert chosen in brain.memory

        # After outcome recording, memory is updated with decision_id key
        brain.record_outcome(decision_id=decision_id, expected=0.5, actual=1.0)
        assert decision_id in brain.memory

    def test_concurrent_decides_not_allowed(self):
        from another_intelligence.state import ActivityPhase

        brain = DigitalBrain()
        brain._state.transition_to(ActivityPhase.PROPOSING)
        with pytest.raises(RuntimeError, match="already active"):
            brain.decide(query="Should not run.")


class TestEdgeCases:
    """Boundary conditions and error paths."""

    def test_empty_options_raises(self):
        brain = DigitalBrain()
        with pytest.raises(ValueError, match="options must not be empty"):
            brain.decide(query="What next?", options=[])

    def test_single_option_is_always_chosen(self):
        brain = DigitalBrain()
        result = brain.decide(query="Confirm?", options=["confirm"])
        assert result["chosen_action"] == "confirm"

    def test_very_long_query_does_not_crash(self):
        brain = DigitalBrain()
        long_query = "Plan a migration. " * 100
        result = brain.decide(query=long_query)
        assert "chosen_action" in result

    def test_decide_with_unicode_query(self):
        brain = DigitalBrain()
        result = brain.decide(query="What is the best café in Paris?")
        assert "chosen_action" in result

    def test_repeated_identical_queries_produce_consistent_structure(self):
        brain = DigitalBrain()
        results = [brain.decide(query="Same query.") for _ in range(3)]
        assert all("chosen_action" in r for r in results)
        assert all(r["options"] == results[0]["options"] for r in results)
