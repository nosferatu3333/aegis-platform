from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from aegis_os.resources.errors import (
    ResourceErrorCode,
    ResourceValidationError,
)

RESOURCE_SCHEMA_VERSION = "1.0"
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
PROHIBITED_SECRET_KEYS = {
    "password",
    "secret",
    "token",
    "api_key",
    "access_key",
    "private_key",
    "credential_value",
}


class ResourceCategory(str, Enum):
    INFORMATION = "information"
    ARTIFACT = "artifact"
    COLLECTION = "collection"
    COMPUTATIONAL = "computational"
    SERVICE = "service"
    COMMUNICATION = "communication"
    HUMAN = "human"
    AGENT = "agent"
    ORGANIZATIONAL = "organizational"
    PHYSICAL = "physical"
    LOGICAL = "logical"
    GOVERNANCE = "governance"
    CREDENTIAL_REFERENCE = "credential_reference"


class ResourceLifecycleStatus(str, Enum):
    DECLARED = "declared"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RESTRICTED = "restricted"
    STALE = "stale"
    ARCHIVED = "archived"
    DELETED = "deleted"
    INVALID = "invalid"


class ResourceResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"
    DENIED = "denied"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"


class ConstraintStrength(str, Enum):
    REQUIRED = "required"
    PREFERRED = "preferred"


class Cardinality(str, Enum):
    ONE = "one"
    ZERO_OR_ONE = "zero_or_one"
    ONE_OR_MORE = "one_or_more"
    ZERO_OR_MORE = "zero_or_more"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    DECLARED = "declared"
    VERIFIED = "verified"
    REJECTED = "rejected"


class RelationType(str, Enum):
    CONTAINS = "contains"
    BELONGS_TO = "belongs_to"
    DERIVED_FROM = "derived_from"
    VERSION_OF = "version_of"
    PRODUCED_BY = "produced_by"
    CONSUMED_BY = "consumed_by"
    GOVERNED_BY = "governed_by"
    OWNED_BY = "owned_by"
    ACCESSIBLE_THROUGH = "accessible_through"
    DEPENDS_ON = "depends_on"
    SUPERSEDES = "supersedes"
    REFERENCES = "references"
    RELATED_TO = "related_to"


SUPPORTED_CONSTRAINT_KINDS = frozenset(
    {
        "namespace_equals",
        "owner_equals",
        "authority_equals",
        "tenant_equals",
        "trust_level_equals",
        "version_equals",
        "revision_equals",
        "classification_contains",
        "location_environment_equals",
        "location_available",
    }
)


def validate_identifier(
    value: str,
    field_name: str,
    *,
    code: ResourceErrorCode = ResourceErrorCode.INVALID_IDENTIFIER,
) -> str:
    if not isinstance(value, str) or not IDENTIFIER_PATTERN.fullmatch(value):
        raise ResourceValidationError(
            code,
            f"{field_name} must be a valid resource identifier.",
        )
    return value


def _validate_schema_version(value: str) -> None:
    if value != RESOURCE_SCHEMA_VERSION:
        raise ResourceValidationError(
            ResourceErrorCode.UNSUPPORTED_SCHEMA_VERSION,
            "Unsupported resource schema version.",
        )


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ResourceValidationError(
            ResourceErrorCode.INVALID_TYPE,
            f"{field_name} must be a non-blank string.",
        )


def _unique_identifiers(
    values: tuple[str, ...],
    field_name: str,
    *,
    code: ResourceErrorCode = ResourceErrorCode.INVALID_DESCRIPTOR,
) -> None:
    for value in values:
        validate_identifier(value, field_name, code=code)
    if len(values) != len(set(values)):
        raise ResourceValidationError(
            code,
            f"{field_name} must contain unique identifiers.",
        )


def _validate_timestamp(value: datetime | None, field_name: str) -> None:
    if value is not None and (not isinstance(value, datetime) or value.tzinfo is None):
        raise ResourceValidationError(
            ResourceErrorCode.INVALID_DESCRIPTOR,
            f"{field_name} must be timezone-aware.",
        )


def _json_safe(value: Any, *, path: str = "value") -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        _validate_timestamp(value, path)
        return value.isoformat()
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ResourceValidationError(
                    ResourceErrorCode.INVALID_DESCRIPTOR,
                    "Mapping keys must be strings.",
                )
            if key.lower() in PROHIBITED_SECRET_KEYS:
                raise ResourceValidationError(
                    ResourceErrorCode.SECRET_VALUE_PROHIBITED,
                    "Secret-bearing fields are prohibited.",
                )
            result[key] = _json_safe(item, path=f"{path}.{key}")
        return result
    if isinstance(value, (tuple, list)):
        return [_json_safe(item, path=path) for item in value]
    raise ResourceValidationError(
        ResourceErrorCode.INVALID_DESCRIPTOR,
        f"{path} must contain only JSON-compatible values.",
    )


def _copy_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ResourceValidationError(
            ResourceErrorCode.INVALID_DESCRIPTOR,
            "Metadata and provenance must be mappings.",
        )
    return _json_safe(value)


def _serialize(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (tuple, list)):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class ResourceType:
    type_id: str
    name: str
    category: ResourceCategory
    description: str
    capability_ids: tuple[str, ...] = ()
    parent_type_id: str | None = None
    schema_version: str = RESOURCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_identifier(
            self.type_id,
            "type_id",
            code=ResourceErrorCode.INVALID_TYPE,
        )
        _require_text(self.name, "name")
        _require_text(self.description, "description")
        _unique_identifiers(
            self.capability_ids,
            "capability_ids",
            code=ResourceErrorCode.INVALID_TYPE,
        )
        if self.parent_type_id is not None:
            validate_identifier(
                self.parent_type_id,
                "parent_type_id",
                code=ResourceErrorCode.INVALID_TYPE,
            )
            if self.parent_type_id == self.type_id:
                raise ResourceValidationError(
                    ResourceErrorCode.INVALID_TYPE,
                    "A resource type cannot be its own parent.",
                )
        _validate_schema_version(self.schema_version)

    def to_dict(self) -> dict[str, Any]:
        return _contract_dict(self)


@dataclass(frozen=True)
class ResourceCapability:
    capability_id: str
    name: str
    operation_class: str
    required_permissions: tuple[str, ...] = ()
    side_effecting: bool = False
    simulation_supported: bool = True
    description: str = ""
    schema_version: str = RESOURCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_identifier(self.capability_id, "capability_id")
        _require_text(self.name, "name")
        validate_identifier(self.operation_class, "operation_class")
        _unique_identifiers(
            self.required_permissions,
            "required_permissions",
        )
        if self.description:
            _require_text(self.description, "description")
        _validate_schema_version(self.schema_version)

    def to_dict(self) -> dict[str, Any]:
        return _contract_dict(self)


@dataclass(frozen=True)
class ResourceIdentity:
    resource_id: str
    namespace: str
    type_id: str
    name: str
    owner_id: str | None = None
    authority_id: str | None = None
    tenant_id: str | None = None
    lifecycle_status: ResourceLifecycleStatus = ResourceLifecycleStatus.DECLARED
    schema_version: str = RESOURCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_identifier(self.resource_id, "resource_id")
        validate_identifier(self.namespace, "namespace")
        validate_identifier(self.type_id, "type_id")
        _require_text(self.name, "name")
        for field_name in ("owner_id", "authority_id", "tenant_id"):
            value = getattr(self, field_name)
            if value is not None:
                validate_identifier(value, field_name)
        _validate_schema_version(self.schema_version)

    @property
    def key(self) -> tuple[str, str]:
        return (self.namespace, self.resource_id)

    def to_reference(
        self,
        *,
        version: str | None = None,
        revision: str | None = None,
        resolution_id: str | None = None,
    ) -> ResourceReference:
        return ResourceReference(
            resource_id=self.resource_id,
            namespace=self.namespace,
            version=version,
            revision=revision,
            resolution_id=resolution_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return _contract_dict(self)


@dataclass(frozen=True)
class ResourceReference:
    resource_id: str
    namespace: str
    version: str | None = None
    revision: str | None = None
    resolution_id: str | None = None
    schema_version: str = RESOURCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_identifier(
            self.resource_id,
            "resource_id",
            code=ResourceErrorCode.INVALID_REFERENCE,
        )
        validate_identifier(
            self.namespace,
            "namespace",
            code=ResourceErrorCode.INVALID_REFERENCE,
        )
        if self.resolution_id is not None:
            validate_identifier(
                self.resolution_id,
                "resolution_id",
                code=ResourceErrorCode.INVALID_REFERENCE,
            )
        for field_name in ("version", "revision"):
            value = getattr(self, field_name)
            if value is not None:
                _require_text(value, field_name)
        _validate_schema_version(self.schema_version)

    @property
    def key(self) -> tuple[str, str]:
        return (self.namespace, self.resource_id)

    def to_dict(self) -> dict[str, Any]:
        return _contract_dict(self)


@dataclass(frozen=True)
class ResourceLocation:
    location_id: str
    environment_id: str
    locator: str
    provider: str | None = None
    scope: str | None = None
    region: str | None = None
    is_local: bool = False
    is_logical: bool = True
    available: bool = True
    version: str | None = None
    revision: str | None = None
    credential_reference: str | None = None

    def __post_init__(self) -> None:
        validate_identifier(self.location_id, "location_id")
        validate_identifier(self.environment_id, "environment_id")
        _require_text(self.locator, "locator")
        for field_name in (
            "provider",
            "scope",
            "region",
            "version",
            "revision",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _require_text(value, field_name)
        if self.credential_reference is not None:
            validate_identifier(
                self.credential_reference,
                "credential_reference",
            )

    def to_dict(self) -> dict[str, Any]:
        return _contract_dict(self)


@dataclass(frozen=True)
class ResourceState:
    status: ResourceLifecycleStatus
    version: str | None = None
    revision: str | None = None
    content_hash: str | None = None
    observed_at: datetime | None = None
    valid_until: datetime | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    source_reference: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("version", "revision", "content_hash"):
            value = getattr(self, field_name)
            if value is not None:
                _require_text(value, field_name)
        _validate_timestamp(self.observed_at, "observed_at")
        _validate_timestamp(self.valid_until, "valid_until")
        if (
            self.observed_at is not None
            and self.valid_until is not None
            and self.valid_until < self.observed_at
        ):
            raise ResourceValidationError(
                ResourceErrorCode.INVALID_DESCRIPTOR,
                "valid_until cannot precede observed_at.",
            )
        if self.source_reference is not None:
            validate_identifier(
                self.source_reference,
                "source_reference",
            )

    def to_dict(self) -> dict[str, Any]:
        return _contract_dict(self)


@dataclass(frozen=True)
class ResourceRelation:
    relation_id: str
    relation_type: RelationType | str
    source: ResourceReference
    target: ResourceReference
    provenance_reference: str | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    def __post_init__(self) -> None:
        validate_identifier(
            self.relation_id,
            "relation_id",
            code=ResourceErrorCode.INVALID_RELATION,
        )
        relation_value = (
            self.relation_type.value
            if isinstance(self.relation_type, RelationType)
            else self.relation_type
        )
        validate_identifier(
            relation_value,
            "relation_type",
            code=ResourceErrorCode.INVALID_RELATION,
        )
        if (
            self.source.key == self.target.key
            and relation_value != RelationType.RELATED_TO.value
        ):
            raise ResourceValidationError(
                ResourceErrorCode.INVALID_RELATION,
                "Only related_to may be a self-relation.",
            )
        if self.provenance_reference is not None:
            validate_identifier(
                self.provenance_reference,
                "provenance_reference",
                code=ResourceErrorCode.INVALID_RELATION,
            )

    def to_dict(self) -> dict[str, Any]:
        return _contract_dict(self)


@dataclass(frozen=True)
class ResourceDescriptor:
    identity: ResourceIdentity
    state: ResourceState
    capability_ids: tuple[str, ...] = ()
    permission_ids: tuple[str, ...] = ()
    locations: tuple[ResourceLocation, ...] = ()
    relations: tuple[ResourceRelation, ...] = ()
    classification_labels: tuple[str, ...] = ()
    trust_level: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = RESOURCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _unique_identifiers(self.capability_ids, "capability_ids")
        _unique_identifiers(self.permission_ids, "permission_ids")
        _unique_identifiers(
            self.classification_labels,
            "classification_labels",
        )
        _unique_object_ids(
            self.locations,
            "location_id",
            "locations",
        )
        _unique_object_ids(
            self.relations,
            "relation_id",
            "relations",
        )
        if self.identity.lifecycle_status is not self.state.status:
            raise ResourceValidationError(
                ResourceErrorCode.INVALID_DESCRIPTOR,
                "Identity and state lifecycle statuses must match.",
            )
        if self.trust_level is not None:
            validate_identifier(self.trust_level, "trust_level")
        _validate_timestamp(self.created_at, "created_at")
        _validate_timestamp(self.updated_at, "updated_at")
        if (
            self.created_at is not None
            and self.updated_at is not None
            and self.updated_at < self.created_at
        ):
            raise ResourceValidationError(
                ResourceErrorCode.INVALID_DESCRIPTOR,
                "updated_at cannot precede created_at.",
            )
        object.__setattr__(
            self,
            "provenance",
            _copy_mapping(self.provenance),
        )
        object.__setattr__(
            self,
            "metadata",
            _copy_mapping(self.metadata),
        )
        _validate_schema_version(self.schema_version)

    @property
    def reference(self) -> ResourceReference:
        return self.identity.to_reference(
            version=self.state.version,
            revision=self.state.revision,
        )

    def to_dict(self) -> dict[str, Any]:
        return _contract_dict(self)


@dataclass(frozen=True)
class ResourceConstraint:
    constraint_id: str
    kind: str
    value: str | int | float | bool
    strength: ConstraintStrength = ConstraintStrength.REQUIRED

    def __post_init__(self) -> None:
        validate_identifier(
            self.constraint_id,
            "constraint_id",
            code=ResourceErrorCode.INVALID_CONSTRAINT,
        )
        validate_identifier(
            self.kind,
            "kind",
            code=ResourceErrorCode.INVALID_CONSTRAINT,
        )
        if self.value is None or not isinstance(
            self.value,
            (str, int, float, bool),
        ):
            raise ResourceValidationError(
                ResourceErrorCode.INVALID_CONSTRAINT,
                "Constraint value must be a JSON scalar.",
            )

    @property
    def supported(self) -> bool:
        return self.kind in SUPPORTED_CONSTRAINT_KINDS

    def to_dict(self) -> dict[str, Any]:
        return _contract_dict(self)


@dataclass(frozen=True)
class ResourceRequirement:
    requirement_id: str
    type_ids: tuple[str, ...]
    required_capability_ids: tuple[str, ...] = ()
    required_permission_ids: tuple[str, ...] = ()
    constraints: tuple[ResourceConstraint, ...] = ()
    preferred_environment_id: str | None = None
    freshness_required: bool = False
    version: str | None = None
    revision: str | None = None
    minimum_trust_level: str | None = None
    cardinality: Cardinality = Cardinality.ONE
    optional: bool = False
    request_id: str | None = None
    workflow_step_id: str | None = None
    schema_version: str = RESOURCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_identifier(
            self.requirement_id,
            "requirement_id",
            code=ResourceErrorCode.INVALID_REQUIREMENT,
        )
        if not self.type_ids:
            raise ResourceValidationError(
                ResourceErrorCode.INVALID_REQUIREMENT,
                "type_ids must contain at least one type.",
            )
        _unique_identifiers(
            self.type_ids,
            "type_ids",
            code=ResourceErrorCode.INVALID_REQUIREMENT,
        )
        _unique_identifiers(
            self.required_capability_ids,
            "required_capability_ids",
            code=ResourceErrorCode.INVALID_REQUIREMENT,
        )
        _unique_identifiers(
            self.required_permission_ids,
            "required_permission_ids",
            code=ResourceErrorCode.INVALID_REQUIREMENT,
        )
        _unique_object_ids(
            self.constraints,
            "constraint_id",
            "constraints",
            code=ResourceErrorCode.INVALID_REQUIREMENT,
        )
        if self.preferred_environment_id is not None:
            validate_identifier(
                self.preferred_environment_id,
                "preferred_environment_id",
                code=ResourceErrorCode.INVALID_REQUIREMENT,
            )
        for field_name in ("version", "revision"):
            value = getattr(self, field_name)
            if value is not None:
                _require_text(value, field_name)
        if self.minimum_trust_level is not None:
            validate_identifier(
                self.minimum_trust_level,
                "minimum_trust_level",
                code=ResourceErrorCode.INVALID_REQUIREMENT,
            )
        for field_name in ("request_id", "workflow_step_id"):
            value = getattr(self, field_name)
            if value is not None:
                validate_identifier(
                    value,
                    field_name,
                    code=ResourceErrorCode.INVALID_REQUIREMENT,
                )
        _validate_schema_version(self.schema_version)

    def to_dict(self) -> dict[str, Any]:
        return _contract_dict(self)


@dataclass(frozen=True)
class CandidateEvaluation:
    resource_reference: ResourceReference
    eligible: bool
    required_matches: tuple[str, ...] = ()
    preferred_matches: tuple[str, ...] = ()
    rejection_codes: tuple[str, ...] = ()
    rank_key: tuple[str | int | float | bool, ...] = ()

    def __post_init__(self) -> None:
        for values, field_name in (
            (self.required_matches, "required_matches"),
            (self.preferred_matches, "preferred_matches"),
            (self.rejection_codes, "rejection_codes"),
        ):
            if len(values) != len(set(values)):
                raise ResourceValidationError(
                    ResourceErrorCode.INVALID_DESCRIPTOR,
                    f"{field_name} must contain unique values.",
                )

    def to_dict(self) -> dict[str, Any]:
        return _contract_dict(self)


@dataclass(frozen=True)
class ResourceResolution:
    resolution_id: str
    requirement_id: str
    status: ResourceResolutionStatus
    selected_references: tuple[ResourceReference, ...] = ()
    candidate_evaluations: tuple[CandidateEvaluation, ...] = ()
    reason_codes: tuple[str, ...] = ()
    request_id: str | None = None
    workflow_step_id: str | None = None
    schema_version: str = RESOURCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_identifier(self.resolution_id, "resolution_id")
        validate_identifier(self.requirement_id, "requirement_id")
        _unique_object_keys(
            self.selected_references,
            lambda item: item.key,
            "selected_references",
        )
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ResourceValidationError(
                ResourceErrorCode.INVALID_DESCRIPTOR,
                "reason_codes must contain unique values.",
            )
        for field_name in ("request_id", "workflow_step_id"):
            value = getattr(self, field_name)
            if value is not None:
                validate_identifier(value, field_name)
        _validate_schema_version(self.schema_version)

    @property
    def resolved(self) -> bool:
        return self.status is ResourceResolutionStatus.RESOLVED

    def to_dict(self) -> dict[str, Any]:
        return _contract_dict(self)


def _unique_object_ids(
    values: tuple[Any, ...],
    attribute: str,
    field_name: str,
    *,
    code: ResourceErrorCode = ResourceErrorCode.INVALID_DESCRIPTOR,
) -> None:
    identifiers = [getattr(item, attribute) for item in values]
    if len(identifiers) != len(set(identifiers)):
        raise ResourceValidationError(
            code,
            f"{field_name} must contain unique {attribute} values.",
        )


def _unique_object_keys(
    values: tuple[Any, ...],
    key_reader: Any,
    field_name: str,
) -> None:
    keys = [key_reader(item) for item in values]
    if len(keys) != len(set(keys)):
        raise ResourceValidationError(
            ResourceErrorCode.INVALID_DESCRIPTOR,
            f"{field_name} must contain unique resources.",
        )


def _contract_dict(instance: Any) -> dict[str, Any]:
    return {
        field_name: _serialize(getattr(instance, field_name))
        for field_name in instance.__dataclass_fields__
    }
