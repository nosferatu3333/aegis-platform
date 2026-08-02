from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class OpsIntegrationError(RuntimeError):
    """Raised when the live AEGIS OPS capability engine cannot be loaded."""


@dataclass(frozen=True)
class OpsSelectionResult:
    capability: Any
    confidence: float
    score: float
    reasons: tuple[str, ...]
    matched_tags: tuple[str, ...]
    source: str = "aegis-ops"
    source_path: str = ""


class OpsCapabilitySelectorAdapter:
    """Use the live sibling AEGIS OPS loader, registry, and selector in-process."""

    def __init__(self, ops_root: str | Path | None = None) -> None:
        self.ops_root = self._resolve_ops_root(ops_root)
        self.capabilities_directory = (
            self.ops_root / "aegis_os" / "capabilities" / "modules"
        )
        self._loader: Any = None
        self._registry: Any = None
        self._selector: Any = None
        self._load_error: str | None = None

    @property
    def available(self) -> bool:
        try:
            self._ensure_runtime()
        except OpsIntegrationError:
            return False
        return True

    @property
    def diagnostic(self) -> dict[str, Any]:
        return {
            "source": "aegis-ops",
            "available": self.available,
            "ops_root": str(self.ops_root),
            "capabilities_directory": str(self.capabilities_directory),
            "error": self._load_error,
        }

    def select(self, task: str, **_: Any) -> OpsSelectionResult | None:
        self._ensure_runtime()
        capabilities = self._registry.list_all()
        matches = self._selector.rank(task, capabilities, top_n=1)
        if not matches:
            return None

        match = matches[0]
        meaningful_terms = {
            term
            for term in match.matched_terms
            if term not in {
                "a", "an", "and", "are", "as", "at", "be", "by",
                "for", "from", "in", "is", "it", "of", "on", "or",
                "that", "the", "to", "with",
            }
        }
        if match.score < 5 or not meaningful_terms:
            return None
        max_score = max(1, len(match.capability.search_terms()) * 2)
        confidence = min(1.0, max(0.0, match.score / max_score))
        reasons = tuple(
            [f"Live OPS score: {match.score}"]
            + [f"Matched term: {term}" for term in sorted(meaningful_terms)]
        )
        tags = tuple(
            sorted(
                {
                    str(tag)
                    for tag in match.capability.tags
                    if str(tag).strip().lower() in match.matched_terms
                }
            )
        )
        return OpsSelectionResult(
            capability=match.capability,
            confidence=confidence,
            score=float(match.score),
            reasons=reasons,
            matched_tags=tags,
            source_path=str(self.ops_root),
        )

    def _ensure_runtime(self) -> None:
        if self._selector is not None:
            return
        if not self.capabilities_directory.is_dir():
            self._load_error = (
                f"OPS capability directory does not exist: "
                f"{self.capabilities_directory}"
            )
            raise OpsIntegrationError(self._load_error)

        try:
            import aegis_os as platform_package

            ops_namespace = str(self.ops_root / "aegis_os")
            if ops_namespace not in platform_package.__path__:
                platform_package.__path__.append(ops_namespace)

            from aegis_os.capabilities.loader import CapabilityLoader
            from aegis_os.capabilities.registry import CapabilityRegistry
            from aegis_os.capabilities.selector import (
                CapabilitySelectionPolicy,
                CapabilitySelector,
            )

            loader = CapabilityLoader()
            capabilities = loader.load_valid_capabilities(
                self.capabilities_directory
            )
            if not capabilities:
                raise OpsIntegrationError(
                    "AEGIS OPS loaded zero valid capability modules."
                )

            registry = CapabilityRegistry()
            for capability in capabilities:
                registry.register(capability)

            self._loader = loader
            self._registry = registry
            self._selector = CapabilitySelector(
                CapabilitySelectionPolicy.development()
            )
            self._load_error = None
        except OpsIntegrationError:
            raise
        except Exception as error:  # pragma: no cover - defensive boundary
            self._load_error = f"Unable to initialize AEGIS OPS: {error}"
            raise OpsIntegrationError(self._load_error) from error

    @staticmethod
    def _resolve_ops_root(ops_root: str | Path | None) -> Path:
        configured = ops_root or os.environ.get("AEGIS_OPS_PATH")
        if configured:
            return Path(configured).expanduser().resolve()
        return (Path(__file__).resolve().parents[3] / "aegis-ops").resolve()


class HybridCapabilitySelector:
    """Prefer live OPS selection and retain bounded legacy fallback."""

    def __init__(self, ops_selector: Any, fallback_selector: Any) -> None:
        self.ops_selector = ops_selector
        self.fallback_selector = fallback_selector

    def select(self, task: str, **context: Any) -> Any:
        required = {
            str(value).strip().lower()
            for value in context.get("required_capabilities", ())
        }
        live_domains = {"development", "planning", "software-development"}
        live_selection = None
        if required.intersection(live_domains):
            try:
                live_selection = self.ops_selector.select(task, **context)
            except OpsIntegrationError:
                live_selection = None
        if live_selection is not None:
            return live_selection
        return self.fallback_selector.select(task, **context)
