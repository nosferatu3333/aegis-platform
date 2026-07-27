import pytest

from aegis_os.resources import (
    ResourceCatalog,
    ResourceCategory,
    ResourceDescriptor,
    ResourceIdentity,
    ResourceLifecycleStatus,
    ResourceLocation,
    ResourceState,
    ResourceType,
    VerificationStatus,
)


@pytest.fixture
def dataset_type():
    return ResourceType(
        type_id="type:dataset",
        name="Dataset",
        category=ResourceCategory.INFORMATION,
        description="A deterministic synthetic dataset.",
        capability_ids=("capability:read", "capability:inspect"),
    )


def make_descriptor(
    resource_id,
    *,
    namespace="workspace:demo",
    type_id="type:dataset",
    status=ResourceLifecycleStatus.AVAILABLE,
    capabilities=("capability:read",),
    permissions=("permission:read",),
    owner_id="owner:aegis",
    authority_id="authority:aegis",
    tenant_id="tenant:demo",
    trust_level="trust:verified",
    version="1.0",
    revision="r1",
    environments=("environment:simulation",),
    labels=("classification:internal",),
):
    return ResourceDescriptor(
        identity=ResourceIdentity(
            resource_id=resource_id,
            namespace=namespace,
            type_id=type_id,
            name=resource_id,
            owner_id=owner_id,
            authority_id=authority_id,
            tenant_id=tenant_id,
            lifecycle_status=status,
        ),
        state=ResourceState(
            status=status,
            version=version,
            revision=revision,
            verification_status=VerificationStatus.DECLARED,
        ),
        capability_ids=capabilities,
        permission_ids=permissions,
        locations=tuple(
            ResourceLocation(
                location_id=f"location:{index}",
                environment_id=environment,
                locator=f"logical://resource/{index}",
                is_logical=True,
                available=True,
            )
            for index, environment in enumerate(environments, start=1)
        ),
        classification_labels=labels,
        trust_level=trust_level,
        provenance={"source": "synthetic-test"},
    )


@pytest.fixture
def descriptor_factory():
    return make_descriptor


@pytest.fixture
def catalog(dataset_type, descriptor_factory):
    return ResourceCatalog(
        resource_types=(dataset_type,),
        descriptors=(
            descriptor_factory("resource:alpha"),
            descriptor_factory("resource:beta"),
        ),
    )
