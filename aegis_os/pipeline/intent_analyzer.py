from __future__ import annotations

import re
from collections.abc import Iterable

from aegis_os.pipeline.models import (
    IntentAnalysis,
    RiskLevel,
    TaskComplexity,
)


class IntentAnalyzer:
    """
    Performs lightweight deterministic mission analysis.

    This first implementation is intentionally rule-based. It creates an
    inspectable baseline before language-model reasoning is introduced.
    """

    INTENT_KEYWORDS: dict[str, set[str]] = {
        "planning": {
            "plan",
            "planning",
            "roadmap",
            "strategy",
            "organize",
            "schedule",
            "prepare",
            "launch",
        },
        "research": {
            "research",
            "investigate",
            "discover",
            "compare",
            "study",
            "find",
            "explore",
        },
        "analysis": {
            "analyze",
            "analysis",
            "evaluate",
            "assess",
            "diagnose",
            "review",
            "understand",
        },
        "development": {
            "build",
            "create",
            "develop",
            "implement",
            "code",
            "design",
            "prototype",
        },
        "execution": {
            "execute",
            "deploy",
            "publish",
            "send",
            "install",
            "run",
            "complete",
        },
        "communication": {
            "write",
            "explain",
            "present",
            "communicate",
            "summarize",
            "document",
            "report",
        },
    }

    INTENT_CAPABILITIES: dict[str, str] = {
        "research": "research",
        "analysis": "analysis",
        "development": "execution",
        "execution": "execution",
    }

    RISK_KEYWORDS: set[str] = {
        "delete",
        "remove",
        "payment",
        "money",
        "legal",
        "medical",
        "security",
        "credential",
        "password",
        "production",
        "deploy",
        "publish",
    }

    EXECUTION_KEYWORDS: set[str] = {
        "execute",
        "deploy",
        "publish",
        "send",
        "install",
        "run",
        "modify",
        "delete",
        "create",
        "build",
        "implement",
    }

    PLANNING_KEYWORDS: set[str] = {
        "plan",
        "strategy",
        "roadmap",
        "organize",
        "launch",
        "prepare",
        "design",
        "build",
        "develop",
    }

    def analyze(self, task: str) -> IntentAnalysis:
        normalized_task = self._normalize(task)

        if not normalized_task:
            raise ValueError("Task cannot be empty.")

        tokens = set(normalized_task.split())
        detected_intents = self._detect_intents(tokens)

        primary_intent = (
            detected_intents[0] if detected_intents else "general_reasoning"
        )

        secondary_intents = tuple(detected_intents[1:])
        required_capabilities = tuple(
            dict.fromkeys(
                self.INTENT_CAPABILITIES[intent]
                for intent in detected_intents
                if intent in self.INTENT_CAPABILITIES
            )
        )
        detected_concepts = tuple(sorted(tokens))

        requires_planning = bool(tokens & self.PLANNING_KEYWORDS)
        requires_execution = bool(tokens & self.EXECUTION_KEYWORDS)

        complexity = self._estimate_complexity(
            normalized_task=normalized_task,
            detected_intents=detected_intents,
            requires_planning=requires_planning,
        )

        risk = self._estimate_risk(tokens)

        return IntentAnalysis(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            required_capabilities=required_capabilities,
            detected_concepts=detected_concepts,
            complexity=complexity,
            risk=risk,
            requires_planning=requires_planning,
            requires_execution=requires_execution,
        )

    def _detect_intents(self, tokens: set[str]) -> list[str]:
        scored_intents: list[tuple[str, int]] = []

        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = len(tokens & keywords)

            if score > 0:
                scored_intents.append((intent, score))

        scored_intents.sort(key=lambda item: (-item[1], item[0]))

        return [intent for intent, _ in scored_intents]

    def _estimate_complexity(
        self,
        normalized_task: str,
        detected_intents: Iterable[str],
        requires_planning: bool,
    ) -> TaskComplexity:
        word_count = len(normalized_task.split())
        intent_count = len(tuple(detected_intents))

        complexity_score = 0

        if word_count >= 8:
            complexity_score += 1

        if word_count >= 20:
            complexity_score += 1

        if intent_count >= 2:
            complexity_score += 1

        if intent_count >= 4:
            complexity_score += 1

        if requires_planning:
            complexity_score += 1

        if complexity_score >= 4:
            return TaskComplexity.HIGH

        if complexity_score >= 2:
            return TaskComplexity.MEDIUM

        return TaskComplexity.LOW

    def _estimate_risk(self, tokens: set[str]) -> RiskLevel:
        matches = tokens & self.RISK_KEYWORDS

        if len(matches) >= 2:
            return RiskLevel.HIGH

        if len(matches) == 1:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    @staticmethod
    def _normalize(task: str) -> str:
        lowered = task.strip().lower()
        cleaned = re.sub(r"[^\w\s-]", " ", lowered)
        return re.sub(r"\s+", " ", cleaned).strip()
