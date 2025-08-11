"""Cost optimisation engine for LLM model selection and batching.

This module defines a ``CostOptimizer`` class that selects the most
appropriate language model for a given task based on factors such as
complexity, urgency and budget.  It can also batch operations to
benefit from provider discounts (e.g. OpenAI’s batch API, which may
offer a 50 % discount【96280605798490†L54-L56】).

In this simplified implementation, the optimiser returns model names
based on simple heuristics and does not maintain real usage history.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence


@dataclass
class CostOptimizer:
    """Select and batch LLM operations to minimise cost."""

    model_costs: Dict[str, float] = field(default_factory=lambda: {
        "gpt-4": 0.03,
        "gpt-3.5-turbo": 0.002,
        "claude-opus": 0.015,
        "grok-free": 0.0,
        "local_llama3": 0.0,
    })
    usage_history: List[Dict[str, float]] = field(default_factory=list)

    def daily_budget_remaining(self) -> float:
        """Return the remaining budget for the current day.

        In a real implementation this would track actual spend versus
        configured budget.  Here we return a fixed large value.
        """
        return 100.0

    def select_model(self, task_type: str, complexity: float, urgency: float) -> str:
        """Select a language model based on task characteristics.

        Parameters
        ----------
        task_type : str
            The type of task (e.g. ``"summarisation"``, ``"analysis"``).
        complexity : float
            Value between 0.0 and 1.0 indicating how complex the task is.
        urgency : float
            Value between 0.0 and 1.0 indicating the urgency of the task.

        Returns
        -------
        str
            The chosen model identifier.
        """
        # Urgent tasks: choose a fast model
        if urgency > 0.8:
            return "gpt-3.5-turbo"
        # Complex tasks: choose a powerful model
        if complexity > 0.7:
            return "claude-opus"
        # Check budget
        if self.daily_budget_remaining() < 1.0:
            return "local_llama3"
        # Default mapping by task type
        mapping = {
            "transcription": "grok-free",
            "summarisation": "gpt-3.5-turbo",
            "analysis": "gpt-4",
        }
        return mapping.get(task_type, "gpt-3.5-turbo")

    def batch_operations(self, operations: Sequence[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:  # type: ignore[name-defined]
        """Group operations into batches to benefit from bulk pricing.

        Parameters
        ----------
        operations : sequence of dict
            Operations to be performed, each with a ``model`` and
            ``complexity``.  This simplified implementation groups
            operations by model name.

        Returns
        -------
        list of list
            A list where each element is a batch (list) of operations
            using the same model.
        """
        batches: Dict[str, List[Dict[str, Any]]] = {}
        for op in operations:
            model = op.get("model", "gpt-3.5-turbo")
            batches.setdefault(model, []).append(op)
        return list(batches.values())