from __future__ import annotations

from enum import Enum


class ResourceErrorCode(str, Enum):
    INVALID_IDENTIFIER = "invalid_identifier"
    INVALID_TYPE = "invalid_type"
    INVALID_REFERENCE = "invalid_reference"
    INVALID_DESCRIPTOR = "invalid_descriptor"
    INVALID_REQUIREMENT = "invalid_requirement"
    INVALID_CONSTRAINT = "invalid_constraint"
    INVALID_RELATION = "invalid_relation"
    DUPLICATE_RESOURCE = "duplicate_resource"
    RESOURCE_NOT_FOUND = "resource_not_found"
    TYPE_NOT_FOUND = "type_not_found"
    CATALOG_CONFLICT = "catalog_conflict"
    SECRET_VALUE_PROHIBITED = "secret_value_prohibited"
    UNSUPPORTED_SCHEMA_VERSION = "unsupported_schema_version"


class ResourceDomainError(ValueError):
    """Stable programmer/configuration error for the resource subsystem."""

    def __init__(self, code: ResourceErrorCode, message: str) -> None:
        self.code = code
        super().__init__(message)


class ResourceValidationError(ResourceDomainError):
    pass


class ResourceCatalogError(ResourceDomainError):
    pass
