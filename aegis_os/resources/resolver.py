from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aegis_os.resources.catalog import ResourceCatalog
from aegis_os.resources.errors import (
    ResourceErrorCode,
    ResourceValidationError,
)
from aegis_os.resources.models import (
    CandidateEvaluation,
    Cardinality,
    ConstraintStrength,
    ResourceConstraint,
    ResourceDescriptor,
    ResourceLifecycleStatus,
    ResourceReference,
    ResourceRequirement,
    ResourceResolution,
    ResourceResolutionStatus,
    SUPPORTED_CONSTRAINT_KINDS,
    validate_identifier,
)


class ReasonCode:
    RESOLVED = "resolved"
    MULTIPLE_RESOLVED = "multiple_resolved"
    OPTIONAL_UNRESOLVED = "optional_unresolved"
    NO_CANDIDATES = "no_candidates"
    AMBIGUOUS_TOP_RANK = "ambiguous_top_rank"
    TYPE_UNSUPPORTED = "type_unsupported"
    CAPABILITY_UNSUPPORTED = "capability_unsupported"
    REQUIRED_CONSTRAINT_UNSUPPORTED = "required_constraint_unsupported"
    PREFERRED_CONSTRAINT_UNSUPPORTED = "preferred_constraint_unsupported"
    PERMISSION_DENIED = "permission_denied"
    RESOURCE_RESTRICTED = "resource_restricted"
    AUTHORITY_MISMATCH = "authority_mismatch"
    TENANT_MISMATCH = "tenant_mismatch"
    OWNER_MISMATCH = "owner_mismatch"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    RESOURCE_DELETED = "resource_deleted"
    RESOURCE_ARCHIVED = "resource_archived"
    RESOURCE_STALE = "resource_stale"
    RESOURCE_INVALID = "resource_invalid"
    STATE_DECLARED = "state_declared"
    TYPE_MISMATCH = "type_mismatch"
    CAPABILITY_MISMATCH = "capability_mismatch"
    PERMISSION_MISMATCH = "permission_mismatch"
    CONSTRAINT_MISMATCH = "constraint_mismatch"
    VERSION_MISMATCH = "version_mismatch"
    REVISION_MISMATCH = "revision_mismatch"
    TRUST_MISMATCH = "trust_mismatch"


@dataclass(frozen=True)
class _EvaluatedCandidate:
    descriptor: ResourceDescriptor
    evaluation: CandidateEvaluation
    preference_score: tuple[int, int]


class ResourceResolver:
    """Deterministic Phase A requirement resolver."""

    def __init__(self, catalog: ResourceCatalog) -> None:
        if not isinstance(catalog, ResourceCatalog):
            raise TypeError("catalog must be a ResourceCatalog.")
        self.catalog = catalog

    def resolve(
        self,
        requirement: ResourceRequirement,
        *,
        resolution_id: str,
    ) -> ResourceResolution:
        if not isinstance(requirement, ResourceRequirement):
            raise ResourceValidationError(
                ResourceErrorCode.INVALID_REQUIREMENT,
                "requirement must be a ResourceRequirement.",
            )
        validate_identifier(resolution_id, "resolution_id")

        unsupported_required = tuple(
            constraint.constraint_id
            for constraint in requirement.constraints
            if (
                constraint.strength is ConstraintStrength.REQUIRED
                and constraint.kind not in SUPPORTED_CONSTRAINT_KINDS
            )
        )
        if unsupported_required:
            return self._resolution(
                requirement,
                resolution_id,
                ResourceResolutionStatus.UNSUPPORTED,
                reason_codes=(
                    ReasonCode.REQUIRED_CONSTRAINT_UNSUPPORTED,
                ),
            )

        registered_types = {
            resource_type.type_id
            for resource_type in self.catalog.list_types()
        }
        supported_requested_types = (
            registered_types & set(requirement.type_ids)
        )
        if not supported_requested_types:
            return self._resolution(
                requirement,
                resolution_id,
                ResourceResolutionStatus.UNSUPPORTED,
                reason_codes=(ReasonCode.TYPE_UNSUPPORTED,),
            )

        evaluated = tuple(
            self._evaluate(descriptor, requirement)
            for descriptor in self.catalog.list_descriptors()
        )
        eligible = sorted(
            (
                candidate
                for candidate in evaluated
                if candidate.evaluation.eligible
            ),
            key=self._sort_key,
        )

        if eligible:
            return self._resolve_eligible(
                requirement,
                resolution_id,
                evaluated,
                eligible,
            )

        status, reason_codes = self._empty_outcome(
            requirement,
            evaluated,
            supported_requested_types,
        )
        if (
            status is ResourceResolutionStatus.UNRESOLVED
            and requirement.cardinality
            in {Cardinality.ZERO_OR_ONE, Cardinality.ZERO_OR_MORE}
        ):
            status = ResourceResolutionStatus.RESOLVED
            reason_codes = (ReasonCode.OPTIONAL_UNRESOLVED,)
        if (
            requirement.optional
            and status is ResourceResolutionStatus.UNRESOLVED
        ):
            status = ResourceResolutionStatus.RESOLVED
            reason_codes = (ReasonCode.OPTIONAL_UNRESOLVED,)

        return self._resolution(
            requirement,
            resolution_id,
            status,
            candidate_evaluations=tuple(
                item.evaluation for item in evaluated
            ),
            reason_codes=reason_codes,
        )

    def _evaluate(
        self,
        descriptor: ResourceDescriptor,
        requirement: ResourceRequirement,
    ) -> _EvaluatedCandidate:
        required_matches: list[str] = []
        preferred_matches: list[str] = []
        rejection_codes: list[str] = []

        if descriptor.identity.type_id in requirement.type_ids:
            required_matches.append(
                f"type:{descriptor.identity.type_id}"
            )
        else:
            rejection_codes.append(ReasonCode.TYPE_MISMATCH)

        missing_capabilities = sorted(
            set(requirement.required_capability_ids)
            - set(descriptor.capability_ids)
        )
        if missing_capabilities:
            rejection_codes.append(ReasonCode.CAPABILITY_MISMATCH)
        else:
            required_matches.extend(
                f"capability:{item}"
                for item in requirement.required_capability_ids
            )

        missing_permissions = sorted(
            set(requirement.required_permission_ids)
            - set(descriptor.permission_ids)
        )
        if missing_permissions:
            rejection_codes.append(ReasonCode.PERMISSION_MISMATCH)
        else:
            required_matches.extend(
                f"permission:{item}"
                for item in requirement.required_permission_ids
            )

        self._evaluate_selectors(
            descriptor,
            requirement,
            required_matches,
            rejection_codes,
        )
        self._evaluate_state(
            descriptor,
            requirement,
            required_matches,
            rejection_codes,
        )

        for constraint in requirement.constraints:
            if not constraint.supported:
                if constraint.strength is ConstraintStrength.PREFERRED:
                    preferred_matches.append(
                        f"unsupported:{constraint.constraint_id}"
                    )
                continue
            matches = self._constraint_matches(
                descriptor,
                constraint,
            )
            if constraint.strength is ConstraintStrength.REQUIRED:
                if matches:
                    required_matches.append(
                        f"constraint:{constraint.constraint_id}"
                    )
                else:
                    rejection_codes.append(
                        self._constraint_rejection_code(constraint)
                    )
            elif matches:
                preferred_matches.append(
                    f"constraint:{constraint.constraint_id}"
                )

        environment_match = int(
            requirement.preferred_environment_id is not None
            and any(
                location.environment_id
                == requirement.preferred_environment_id
                for location in descriptor.locations
            )
        )
        if environment_match:
            preferred_matches.append("preferred_environment")

        preference_score = (
            len(
                [
                    item
                    for item in preferred_matches
                    if not item.startswith("unsupported:")
                ]
            ),
            environment_match,
        )
        reference = descriptor.reference
        evaluation = CandidateEvaluation(
            resource_reference=reference,
            eligible=not rejection_codes,
            required_matches=tuple(required_matches),
            preferred_matches=tuple(preferred_matches),
            rejection_codes=tuple(dict.fromkeys(rejection_codes)),
            rank_key=(
                preference_score[0],
                preference_score[1],
                reference.namespace,
                reference.resource_id,
            ),
        )
        return _EvaluatedCandidate(
            descriptor=descriptor,
            evaluation=evaluation,
            preference_score=preference_score,
        )

    @staticmethod
    def _evaluate_selectors(
        descriptor: ResourceDescriptor,
        requirement: ResourceRequirement,
        required_matches: list[str],
        rejection_codes: list[str],
    ) -> None:
        if requirement.version is not None:
            if descriptor.state.version == requirement.version:
                required_matches.append("version")
            else:
                rejection_codes.append(ReasonCode.VERSION_MISMATCH)
        if requirement.revision is not None:
            if descriptor.state.revision == requirement.revision:
                required_matches.append("revision")
            else:
                rejection_codes.append(ReasonCode.REVISION_MISMATCH)
        if requirement.minimum_trust_level is not None:
            if descriptor.trust_level == requirement.minimum_trust_level:
                required_matches.append("trust_level")
            else:
                rejection_codes.append(ReasonCode.TRUST_MISMATCH)

    @staticmethod
    def _evaluate_state(
        descriptor: ResourceDescriptor,
        requirement: ResourceRequirement,
        required_matches: list[str],
        rejection_codes: list[str],
    ) -> None:
        status = descriptor.state.status
        if status is ResourceLifecycleStatus.AVAILABLE:
            required_matches.append("state:available")
        elif status is ResourceLifecycleStatus.DECLARED:
            required_matches.append(ReasonCode.STATE_DECLARED)
        elif status is ResourceLifecycleStatus.STALE:
            if requirement.freshness_required:
                rejection_codes.append(ReasonCode.RESOURCE_STALE)
            else:
                required_matches.append("state:stale_allowed")
        elif status is ResourceLifecycleStatus.RESTRICTED:
            rejection_codes.append(ReasonCode.RESOURCE_RESTRICTED)
        elif status is ResourceLifecycleStatus.UNAVAILABLE:
            rejection_codes.append(ReasonCode.RESOURCE_UNAVAILABLE)
        elif status is ResourceLifecycleStatus.ARCHIVED:
            rejection_codes.append(ReasonCode.RESOURCE_ARCHIVED)
        elif status is ResourceLifecycleStatus.DELETED:
            rejection_codes.append(ReasonCode.RESOURCE_DELETED)
        else:
            rejection_codes.append(ReasonCode.RESOURCE_INVALID)

    @staticmethod
    def _constraint_matches(
        descriptor: ResourceDescriptor,
        constraint: ResourceConstraint,
    ) -> bool:
        identity = descriptor.identity
        state = descriptor.state
        handlers: dict[str, Any] = {
            "namespace_equals": lambda: identity.namespace
            == constraint.value,
            "owner_equals": lambda: identity.owner_id == constraint.value,
            "authority_equals": lambda: identity.authority_id
            == constraint.value,
            "tenant_equals": lambda: identity.tenant_id == constraint.value,
            "trust_level_equals": lambda: descriptor.trust_level
            == constraint.value,
            "version_equals": lambda: state.version == constraint.value,
            "revision_equals": lambda: state.revision == constraint.value,
            "classification_contains": lambda: constraint.value
            in descriptor.classification_labels,
            "location_environment_equals": lambda: any(
                location.environment_id == constraint.value
                for location in descriptor.locations
            ),
            "location_available": lambda: any(
                location.available == constraint.value
                for location in descriptor.locations
            ),
        }
        return bool(handlers[constraint.kind]())

    @staticmethod
    def _constraint_rejection_code(
        constraint: ResourceConstraint,
    ) -> str:
        if constraint.kind == "owner_equals":
            return ReasonCode.OWNER_MISMATCH
        if constraint.kind == "authority_equals":
            return ReasonCode.AUTHORITY_MISMATCH
        if constraint.kind == "tenant_equals":
            return ReasonCode.TENANT_MISMATCH
        return ReasonCode.CONSTRAINT_MISMATCH

    @staticmethod
    def _sort_key(
        candidate: _EvaluatedCandidate,
    ) -> tuple[int, int, str, str]:
        reference = candidate.evaluation.resource_reference
        return (
            -candidate.preference_score[0],
            -candidate.preference_score[1],
            reference.namespace,
            reference.resource_id,
        )

    def _resolve_eligible(
        self,
        requirement: ResourceRequirement,
        resolution_id: str,
        evaluated: tuple[_EvaluatedCandidate, ...],
        eligible: list[_EvaluatedCandidate],
    ) -> ResourceResolution:
        single = requirement.cardinality in {
            Cardinality.ONE,
            Cardinality.ZERO_OR_ONE,
        }
        if (
            single
            and len(eligible) > 1
            and eligible[0].preference_score
            == eligible[1].preference_score
        ):
            return self._resolution(
                requirement,
                resolution_id,
                ResourceResolutionStatus.AMBIGUOUS,
                candidate_evaluations=tuple(
                    item.evaluation for item in evaluated
                ),
                reason_codes=(ReasonCode.AMBIGUOUS_TOP_RANK,),
            )

        selected = (
            eligible[:1]
            if single
            else eligible
        )
        reason_code = (
            ReasonCode.RESOLVED
            if len(selected) == 1
            else ReasonCode.MULTIPLE_RESOLVED
        )
        return self._resolution(
            requirement,
            resolution_id,
            ResourceResolutionStatus.RESOLVED,
            selected_references=tuple(
                item.evaluation.resource_reference
                for item in selected
            ),
            candidate_evaluations=tuple(
                item.evaluation for item in evaluated
            ),
            reason_codes=(reason_code,),
        )

    @staticmethod
    def _empty_outcome(
        requirement: ResourceRequirement,
        evaluated: tuple[_EvaluatedCandidate, ...],
        supported_requested_types: set[str],
    ) -> tuple[ResourceResolutionStatus, tuple[str, ...]]:
        relevant = [
            item.evaluation
            for item in evaluated
            if item.descriptor.identity.type_id
            in supported_requested_types
        ]
        rejection_codes = {
            code
            for item in relevant
            for code in item.rejection_codes
        }

        denied_codes = {
            ReasonCode.PERMISSION_MISMATCH,
            ReasonCode.RESOURCE_RESTRICTED,
            ReasonCode.AUTHORITY_MISMATCH,
            ReasonCode.TENANT_MISMATCH,
            ReasonCode.OWNER_MISMATCH,
        }
        unavailable_codes = {
            ReasonCode.RESOURCE_UNAVAILABLE,
            ReasonCode.RESOURCE_DELETED,
            ReasonCode.RESOURCE_ARCHIVED,
            ReasonCode.RESOURCE_STALE,
        }
        if rejection_codes & denied_codes:
            return (
                ResourceResolutionStatus.DENIED,
                (ReasonCode.PERMISSION_DENIED,),
            )
        if rejection_codes & unavailable_codes:
            return (
                ResourceResolutionStatus.UNAVAILABLE,
                (
                    sorted(rejection_codes & unavailable_codes)[0],
                ),
            )
        if (
            relevant
            and all(
                ReasonCode.CAPABILITY_MISMATCH
                in item.rejection_codes
                for item in relevant
            )
        ):
            return (
                ResourceResolutionStatus.UNSUPPORTED,
                (ReasonCode.CAPABILITY_UNSUPPORTED,),
            )
        if not relevant:
            return (
                ResourceResolutionStatus.UNRESOLVED,
                (ReasonCode.NO_CANDIDATES,),
            )
        return (
            ResourceResolutionStatus.UNRESOLVED,
            (ReasonCode.NO_CANDIDATES,),
        )

    @staticmethod
    def _resolution(
        requirement: ResourceRequirement,
        resolution_id: str,
        status: ResourceResolutionStatus,
        *,
        selected_references: tuple[ResourceReference, ...] = (),
        candidate_evaluations: tuple[CandidateEvaluation, ...] = (),
        reason_codes: tuple[str, ...] = (),
    ) -> ResourceResolution:
        return ResourceResolution(
            resolution_id=resolution_id,
            requirement_id=requirement.requirement_id,
            status=status,
            selected_references=tuple(
                ResourceReference(
                    resource_id=reference.resource_id,
                    namespace=reference.namespace,
                    version=reference.version,
                    revision=reference.revision,
                    resolution_id=resolution_id,
                )
                for reference in selected_references
            ),
            candidate_evaluations=candidate_evaluations,
            reason_codes=reason_codes,
            request_id=requirement.request_id,
            workflow_step_id=requirement.workflow_step_id,
        )
