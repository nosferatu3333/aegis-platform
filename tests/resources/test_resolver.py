import json

import pytest

from aegis_os.resources import (
    Cardinality,
    ConstraintStrength,
    ReasonCode,
    ResourceCatalog,
    ResourceConstraint,
    ResourceLifecycleStatus,
    ResourceRequirement,
    ResourceResolutionStatus,
    ResourceResolver,
)


def requirement(**overrides):
    values = {
        "requirement_id": "requirement:dataset",
        "type_ids": ("type:dataset",),
        "required_capability_ids": ("capability:read",),
        "required_permission_ids": ("permission:read",),
        "cardinality": Cardinality.ONE,
    }
    values.update(overrides)
    return ResourceRequirement(**values)


def resolve(catalog, item=None, resolution_id="resolution:1"):
    return ResourceResolver(catalog).resolve(
        item or requirement(),
        resolution_id=resolution_id,
    )


def test_single_resolution_and_correlation(dataset_type, descriptor_factory):
    catalog = ResourceCatalog(
        resource_types=(dataset_type,),
        descriptors=(descriptor_factory("resource:only"),),
    )
    item = requirement(
        request_id="request:1",
        workflow_step_id="step:1",
    )

    result = resolve(catalog, item)

    assert result.status is ResourceResolutionStatus.RESOLVED
    assert result.resolved is True
    assert result.reason_codes == (ReasonCode.RESOLVED,)
    assert result.request_id == "request:1"
    assert result.workflow_step_id == "step:1"
    assert result.selected_references[0].resolution_id == "resolution:1"


def test_equal_top_candidates_are_ambiguous(catalog):
    result = resolve(catalog)

    assert result.status is ResourceResolutionStatus.AMBIGUOUS
    assert result.selected_references == ()
    assert result.reason_codes == (ReasonCode.AMBIGUOUS_TOP_RANK,)


def test_preference_resolves_semantic_ambiguity(
    dataset_type,
    descriptor_factory,
):
    catalog = ResourceCatalog(
        resource_types=(dataset_type,),
        descriptors=(
            descriptor_factory(
                "resource:other",
                environments=("environment:other",),
            ),
            descriptor_factory(
                "resource:preferred",
                environments=("environment:preferred",),
            ),
        ),
    )

    result = resolve(
        catalog,
        requirement(preferred_environment_id="environment:preferred"),
    )

    assert result.status is ResourceResolutionStatus.RESOLVED
    assert result.selected_references[0].resource_id == "resource:preferred"


@pytest.mark.parametrize(
    "cardinality",
    [Cardinality.ONE_OR_MORE, Cardinality.ZERO_OR_MORE],
)
def test_multiple_cardinalities_select_all_in_canonical_order(
    catalog,
    cardinality,
):
    result = resolve(
        catalog,
        requirement(cardinality=cardinality),
    )

    assert result.status is ResourceResolutionStatus.RESOLVED
    assert [reference.resource_id for reference in result.selected_references] == [
        "resource:alpha",
        "resource:beta",
    ]
    assert result.reason_codes == (ReasonCode.MULTIPLE_RESOLVED,)


@pytest.mark.parametrize(
    "cardinality",
    [Cardinality.ZERO_OR_ONE, Cardinality.ZERO_OR_MORE],
)
def test_zero_allowed_cardinality_resolves_empty(
    dataset_type,
    cardinality,
):
    catalog = ResourceCatalog(resource_types=(dataset_type,))

    result = resolve(
        catalog,
        requirement(cardinality=cardinality),
    )

    assert result.status is ResourceResolutionStatus.RESOLVED
    assert result.selected_references == ()


def test_optional_requirement_may_resolve_empty(dataset_type):
    catalog = ResourceCatalog(resource_types=(dataset_type,))

    result = resolve(catalog, requirement(optional=True))

    assert result.status is ResourceResolutionStatus.RESOLVED
    assert result.selected_references == ()
    assert result.reason_codes == (ReasonCode.OPTIONAL_UNRESOLVED,)


def test_permission_mismatch_is_denied(dataset_type, descriptor_factory):
    catalog = ResourceCatalog(
        resource_types=(dataset_type,),
        descriptors=(
            descriptor_factory(
                "resource:no-permission",
                permissions=(),
            ),
        ),
    )

    result = resolve(catalog)

    assert result.status is ResourceResolutionStatus.DENIED
    assert result.reason_codes == (ReasonCode.PERMISSION_DENIED,)
    assert result.candidate_evaluations[0].rejection_codes == (
        ReasonCode.PERMISSION_MISMATCH,
    )


@pytest.mark.parametrize(
    ("status", "expected_reason"),
    [
        (
            ResourceLifecycleStatus.UNAVAILABLE,
            ReasonCode.RESOURCE_UNAVAILABLE,
        ),
        (
            ResourceLifecycleStatus.DELETED,
            ReasonCode.RESOURCE_DELETED,
        ),
        (
            ResourceLifecycleStatus.ARCHIVED,
            ReasonCode.RESOURCE_ARCHIVED,
        ),
    ],
)
def test_unavailable_states_are_distinct_from_absent(
    dataset_type,
    descriptor_factory,
    status,
    expected_reason,
):
    catalog = ResourceCatalog(
        resource_types=(dataset_type,),
        descriptors=(descriptor_factory("resource:state", status=status),),
    )

    result = resolve(catalog)

    assert result.status is ResourceResolutionStatus.UNAVAILABLE
    assert result.reason_codes == (expected_reason,)
    assert len(result.candidate_evaluations) == 1


def test_stale_resource_depends_on_freshness(
    dataset_type,
    descriptor_factory,
):
    catalog = ResourceCatalog(
        resource_types=(dataset_type,),
        descriptors=(
            descriptor_factory(
                "resource:stale",
                status=ResourceLifecycleStatus.STALE,
            ),
        ),
    )

    allowed = resolve(catalog, requirement(freshness_required=False))
    rejected = resolve(catalog, requirement(freshness_required=True))

    assert allowed.status is ResourceResolutionStatus.RESOLVED
    assert rejected.status is ResourceResolutionStatus.UNAVAILABLE
    assert rejected.reason_codes == (ReasonCode.RESOURCE_STALE,)


def test_unknown_type_and_capability_are_unsupported(
    dataset_type,
    descriptor_factory,
):
    catalog = ResourceCatalog(
        resource_types=(dataset_type,),
        descriptors=(descriptor_factory("resource:one"),),
    )

    unknown_type = resolve(
        catalog,
        requirement(type_ids=("type:unknown",)),
    )
    unknown_capability = resolve(
        catalog,
        requirement(required_capability_ids=("capability:unknown",)),
    )

    assert unknown_type.status is ResourceResolutionStatus.UNSUPPORTED
    assert unknown_type.reason_codes == (ReasonCode.TYPE_UNSUPPORTED,)
    assert unknown_capability.status is ResourceResolutionStatus.UNSUPPORTED
    assert unknown_capability.reason_codes == (ReasonCode.CAPABILITY_UNSUPPORTED,)


def test_required_constraint_and_namespace_filtering(
    dataset_type,
    descriptor_factory,
):
    catalog = ResourceCatalog(
        resource_types=(dataset_type,),
        descriptors=(
            descriptor_factory(
                "resource:other",
                namespace="workspace:other",
            ),
            descriptor_factory(
                "resource:target",
                namespace="workspace:target",
            ),
        ),
    )
    constraint = ResourceConstraint(
        constraint_id="constraint:namespace",
        kind="namespace_equals",
        value="workspace:target",
    )

    result = resolve(
        catalog,
        requirement(constraints=(constraint,)),
    )

    assert result.status is ResourceResolutionStatus.RESOLVED
    assert result.selected_references[0].namespace == "workspace:target"


def test_unsupported_required_constraint_returns_result(catalog):
    constraint = ResourceConstraint(
        constraint_id="constraint:unknown",
        kind="extension:unknown",
        value=True,
        strength=ConstraintStrength.REQUIRED,
    )

    result = resolve(
        catalog,
        requirement(constraints=(constraint,)),
    )

    assert result.status is ResourceResolutionStatus.UNSUPPORTED
    assert result.reason_codes == (ReasonCode.REQUIRED_CONSTRAINT_UNSUPPORTED,)


def test_unsupported_preference_is_recorded_but_not_scored(
    dataset_type,
    descriptor_factory,
):
    catalog = ResourceCatalog(
        resource_types=(dataset_type,),
        descriptors=(descriptor_factory("resource:one"),),
    )
    constraint = ResourceConstraint(
        constraint_id="constraint:future",
        kind="extension:future",
        value=True,
        strength=ConstraintStrength.PREFERRED,
    )

    result = resolve(
        catalog,
        requirement(constraints=(constraint,)),
    )

    assert result.status is ResourceResolutionStatus.RESOLVED
    assert result.candidate_evaluations[0].preferred_matches == (
        "unsupported:constraint:future",
    )


def test_version_revision_and_trust_are_exact(
    dataset_type,
    descriptor_factory,
):
    catalog = ResourceCatalog(
        resource_types=(dataset_type,),
        descriptors=(descriptor_factory("resource:one"),),
    )

    matching = resolve(
        catalog,
        requirement(
            version="1.0",
            revision="r1",
            minimum_trust_level="trust:verified",
        ),
    )
    mismatch = resolve(
        catalog,
        requirement(version="2.0"),
    )

    assert matching.status is ResourceResolutionStatus.RESOLVED
    assert mismatch.status is ResourceResolutionStatus.UNRESOLVED
    assert mismatch.candidate_evaluations[0].rejection_codes == (
        ReasonCode.VERSION_MISMATCH,
    )


def test_repeated_identical_resolution_serializes_identically(catalog):
    resolver = ResourceResolver(catalog)
    item = requirement(cardinality=Cardinality.ONE_OR_MORE)

    first = resolver.resolve(item, resolution_id="resolution:repeat")
    second = resolver.resolve(item, resolution_id="resolution:repeat")

    assert first == second
    assert first.to_dict() == second.to_dict()
    assert json.dumps(first.to_dict(), sort_keys=True) == json.dumps(
        second.to_dict(),
        sort_keys=True,
    )


def test_resolution_does_not_depend_on_registration_order(
    dataset_type,
    descriptor_factory,
):
    alpha = descriptor_factory("resource:alpha")
    beta = descriptor_factory("resource:beta")
    first = ResourceCatalog(
        resource_types=(dataset_type,),
        descriptors=(beta, alpha),
    )
    second = ResourceCatalog(
        resource_types=(dataset_type,),
        descriptors=(alpha, beta),
    )
    item = requirement(cardinality=Cardinality.ONE_OR_MORE)

    assert resolve(first, item).to_dict() == resolve(second, item).to_dict()
