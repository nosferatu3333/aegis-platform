import json
from datetime import datetime, timedelta, timezone

import pytest

from aegis_os.resources import (
    RESOURCE_SCHEMA_VERSION,
    RelationType,
    ResourceCategory,
    ResourceDescriptor,
    ResourceErrorCode,
    ResourceIdentity,
    ResourceLifecycleStatus,
    ResourceReference,
    ResourceRelation,
    ResourceState,
    ResourceType,
    ResourceValidationError,
)


def test_identity_is_namespace_scoped_hashable_and_location_independent():
    first = ResourceIdentity(
        resource_id="resource:report",
        namespace="workspace:one",
        type_id="type:document",
        name="Report",
    )
    same = ResourceIdentity(
        resource_id="resource:report",
        namespace="workspace:one",
        type_id="type:document",
        name="Report",
    )
    other_namespace = ResourceIdentity(
        resource_id="resource:report",
        namespace="workspace:two",
        type_id="type:document",
        name="Report",
    )

    assert first == same
    assert hash(first) == hash(same)
    assert first.key != other_namespace.key
    assert "provider" not in first.to_dict()
    assert "location" not in first.to_dict()


@pytest.mark.parametrize(
    "value",
    ["", "contains space", "slash/value", "x" * 129, "é"],
)
def test_invalid_identifiers_are_rejected(value):
    with pytest.raises(ResourceValidationError) as raised:
        ResourceReference(
            resource_id=value,
            namespace="workspace:test",
        )

    assert raised.value.code is ResourceErrorCode.INVALID_REFERENCE


def test_reference_is_lightweight_and_predictable():
    reference = ResourceReference(
        resource_id="resource:dataset",
        namespace="workspace:test",
        version="1.0",
        revision="r1",
        resolution_id="resolution:1",
    )

    assert reference.to_dict() == {
        "resource_id": "resource:dataset",
        "namespace": "workspace:test",
        "version": "1.0",
        "revision": "r1",
        "resolution_id": "resolution:1",
        "schema_version": "1.0",
    }
    assert "metadata" not in reference.to_dict()
    assert "locator" not in reference.to_dict()


def test_descriptor_copies_nested_metadata_and_serializes_safely(
    descriptor_factory,
):
    metadata = {"nested": {"values": [1, 2]}}
    base = descriptor_factory("resource:copy")
    descriptor = ResourceDescriptor(
        identity=base.identity,
        state=base.state,
        metadata=metadata,
    )
    metadata["nested"]["values"].append(3)
    serialized = descriptor.to_dict()
    serialized["metadata"]["nested"]["values"].append(4)

    assert descriptor.to_dict()["metadata"] == {
        "nested": {"values": [1, 2]}
    }
    assert json.loads(json.dumps(descriptor.to_dict()))["schema_version"] == (
        RESOURCE_SCHEMA_VERSION
    )


@pytest.mark.parametrize(
    "metadata",
    [
        {"token": "value"},
        {"nested": {"api_key": "value"}},
        {"items": [{"private_key": "value"}]},
    ],
)
def test_secret_shaped_metadata_is_rejected(metadata, descriptor_factory):
    base = descriptor_factory("resource:secret")

    with pytest.raises(ResourceValidationError) as raised:
        ResourceDescriptor(
            identity=base.identity,
            state=base.state,
            metadata=metadata,
        )

    assert raised.value.code is ResourceErrorCode.SECRET_VALUE_PROHIBITED
    assert "value" not in str(raised.value)


def test_descriptor_requires_consistent_state(descriptor_factory):
    base = descriptor_factory("resource:state")

    with pytest.raises(ResourceValidationError):
        ResourceDescriptor(
            identity=base.identity,
            state=ResourceState(
                status=ResourceLifecycleStatus.UNAVAILABLE
            ),
        )


def test_resource_state_requires_timezone_and_valid_range():
    naive = datetime(2026, 1, 1)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(ResourceValidationError):
        ResourceState(
            status=ResourceLifecycleStatus.AVAILABLE,
            observed_at=naive,
        )
    with pytest.raises(ResourceValidationError):
        ResourceState(
            status=ResourceLifecycleStatus.AVAILABLE,
            observed_at=now,
            valid_until=now - timedelta(seconds=1),
        )


def test_relation_is_directional_and_rejects_invalid_self_relation():
    source = ResourceReference("resource:a", "workspace:test")
    target = ResourceReference("resource:b", "workspace:test")
    relation = ResourceRelation(
        relation_id="relation:a-b",
        relation_type=RelationType.DERIVED_FROM,
        source=source,
        target=target,
    )

    assert relation.to_dict()["relation_type"] == "derived_from"
    assert relation.source != relation.target

    with pytest.raises(ResourceValidationError) as raised:
        ResourceRelation(
            relation_id="relation:self",
            relation_type=RelationType.DEPENDS_ON,
            source=source,
            target=source,
        )

    assert raised.value.code is ResourceErrorCode.INVALID_RELATION


def test_related_to_may_be_self_relation():
    reference = ResourceReference("resource:a", "workspace:test")

    relation = ResourceRelation(
        relation_id="relation:self",
        relation_type=RelationType.RELATED_TO,
        source=reference,
        target=reference,
    )

    assert relation.source == relation.target


def test_resource_type_rejects_duplicate_capabilities():
    with pytest.raises(ResourceValidationError) as raised:
        ResourceType(
            type_id="type:dataset",
            name="Dataset",
            category=ResourceCategory.INFORMATION,
            description="Dataset.",
            capability_ids=("capability:read", "capability:read"),
        )

    assert raised.value.code is ResourceErrorCode.INVALID_TYPE
