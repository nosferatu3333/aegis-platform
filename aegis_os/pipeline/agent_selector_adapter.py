from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from aegis_os.agents.capability_matcher import CapabilityMatcher


class AgentSelectorAdapter:
    """
    Adapts the existing AgentRegistry and CapabilityMatcher
    to the selector interface expected by the cognitive pipeline.
    """

    def __init__(
        self,
        registry: Any,
        matcher: CapabilityMatcher | None = None,
    ) -> None:
        self.registry = registry
        self.matcher = matcher or CapabilityMatcher()

    def select(
        self,
        task: str | Iterable[str] | None = None,
        *,
        required_capabilities: Iterable[str] | None = None,
        **_: Any,
    ) -> Any:
        """
        Selects the best registered agent/profile.

        Extra keyword arguments are accepted so the adapter remains
        compatible with future pipeline inputs.
        """

        if required_capabilities is None:
            required_capabilities = task

        capabilities = self._normalize_capabilities(required_capabilities)

        profiles = self.registry.list_profiles()

        if not profiles:
            return None

        return self.matcher.select(
            profiles=profiles,
            required_capabilities=capabilities,
        )

    @staticmethod
    def _normalize_capabilities(
        capabilities: Iterable[str] | None,
    ) -> list[str]:
        if capabilities is None:
            return []

        if isinstance(capabilities, str):
            capabilities = (capabilities,)

        normalized = []

        for capability in capabilities:
            value = str(capability).strip().lower()

            if value and value not in normalized:
                normalized.append(value)

        return normalized
