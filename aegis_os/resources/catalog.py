from __future__ import annotations

from collections.abc import Iterable

from aegis_os.resources.errors import (
    ResourceCatalogError,
    ResourceErrorCode,
)
from aegis_os.resources.models import (
    ResourceDescriptor,
    ResourceReference,
    ResourceRequirement,
    ResourceResolution,
    ResourceType,
)


class ResourceCatalog:
    """Explicit deterministic in-memory resource catalog."""

    def __init__(
        self,
        *,
        resource_types: Iterable[ResourceType] = (),
        descriptors: Iterable[ResourceDescriptor] = (),
    ) -> None:
        self._types: dict[str, ResourceType] = {}
        self._descriptors: dict[
            tuple[str, str],
            ResourceDescriptor,
        ] = {}
        for resource_type in resource_types:
            self.register_type(resource_type)
        for descriptor in descriptors:
            self.register(descriptor)

    def register_type(self, resource_type: ResourceType) -> None:
        if not isinstance(resource_type, ResourceType):
            raise ResourceCatalogError(
                ResourceErrorCode.INVALID_TYPE,
                "resource_type must be a ResourceType.",
            )
        if resource_type.type_id in self._types:
            raise ResourceCatalogError(
                ResourceErrorCode.CATALOG_CONFLICT,
                "Resource type is already registered.",
            )
        self._types[resource_type.type_id] = resource_type

    def get_type(self, type_id: str) -> ResourceType:
        try:
            return self._types[type_id]
        except KeyError as error:
            raise ResourceCatalogError(
                ResourceErrorCode.TYPE_NOT_FOUND,
                "Resource type is not registered.",
            ) from error

    def list_types(self) -> tuple[ResourceType, ...]:
        return tuple(
            self._types[type_id]
            for type_id in sorted(self._types)
        )

    def register(self, descriptor: ResourceDescriptor) -> None:
        if not isinstance(descriptor, ResourceDescriptor):
            raise ResourceCatalogError(
                ResourceErrorCode.INVALID_DESCRIPTOR,
                "descriptor must be a ResourceDescriptor.",
            )
        if descriptor.identity.type_id not in self._types:
            raise ResourceCatalogError(
                ResourceErrorCode.TYPE_NOT_FOUND,
                "Descriptor resource type is not registered.",
            )
        key = descriptor.identity.key
        if key in self._descriptors:
            raise ResourceCatalogError(
                ResourceErrorCode.DUPLICATE_RESOURCE,
                "Resource identity is already registered.",
            )
        self._descriptors[key] = descriptor

    def get(self, reference: ResourceReference) -> ResourceDescriptor:
        if not isinstance(reference, ResourceReference):
            raise ResourceCatalogError(
                ResourceErrorCode.INVALID_REFERENCE,
                "reference must be a ResourceReference.",
            )
        try:
            descriptor = self._descriptors[reference.key]
        except KeyError as error:
            raise ResourceCatalogError(
                ResourceErrorCode.RESOURCE_NOT_FOUND,
                "Resource is not registered.",
            ) from error

        if (
            reference.version is not None
            and descriptor.state.version != reference.version
        ):
            raise ResourceCatalogError(
                ResourceErrorCode.RESOURCE_NOT_FOUND,
                "Requested resource version is not registered.",
            )
        if (
            reference.revision is not None
            and descriptor.state.revision != reference.revision
        ):
            raise ResourceCatalogError(
                ResourceErrorCode.RESOURCE_NOT_FOUND,
                "Requested resource revision is not registered.",
            )
        return descriptor

    def list_descriptors(self) -> tuple[ResourceDescriptor, ...]:
        return tuple(
            self._descriptors[key]
            for key in sorted(self._descriptors)
        )

    def resolve(
        self,
        requirement: ResourceRequirement,
        resolution_id: str,
    ) -> ResourceResolution:
        from aegis_os.resources.resolver import ResourceResolver

        return ResourceResolver(self).resolve(
            requirement,
            resolution_id=resolution_id,
        )
