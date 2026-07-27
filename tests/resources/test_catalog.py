import pytest

from aegis_os.resources import (
    ResourceCatalog,
    ResourceCatalogError,
    ResourceErrorCode,
    ResourceReference,
    ResourceType,
)


def test_catalog_lists_types_and_resources_canonically(
    dataset_type,
    descriptor_factory,
):
    second_type = ResourceType(
        type_id="type:artifact",
        name="Artifact",
        category=dataset_type.category,
        description="Artifact type.",
    )
    catalog = ResourceCatalog(
        resource_types=(dataset_type, second_type),
        descriptors=(
            descriptor_factory("resource:z"),
            descriptor_factory(
                "resource:a",
                namespace="workspace:z",
            ),
            descriptor_factory(
                "resource:z",
                namespace="workspace:a",
            ),
        ),
    )

    assert [item.type_id for item in catalog.list_types()] == [
        "type:artifact",
        "type:dataset",
    ]
    assert [item.identity.key for item in catalog.list_descriptors()] == [
        ("workspace:a", "resource:z"),
        ("workspace:demo", "resource:z"),
        ("workspace:z", "resource:a"),
    ]


def test_duplicate_identity_is_rejected(dataset_type, descriptor_factory):
    descriptor = descriptor_factory("resource:duplicate")
    catalog = ResourceCatalog(
        resource_types=(dataset_type,),
        descriptors=(descriptor,),
    )

    with pytest.raises(ResourceCatalogError) as raised:
        catalog.register(descriptor)

    assert raised.value.code is ResourceErrorCode.DUPLICATE_RESOURCE


def test_catalog_requires_registered_type(descriptor_factory):
    catalog = ResourceCatalog()

    with pytest.raises(ResourceCatalogError) as raised:
        catalog.register(descriptor_factory("resource:missing-type"))

    assert raised.value.code is ResourceErrorCode.TYPE_NOT_FOUND


def test_lookup_uses_identity_and_exact_selectors(catalog):
    reference = ResourceReference(
        resource_id="resource:alpha",
        namespace="workspace:demo",
        version="1.0",
        revision="r1",
    )

    assert catalog.get(reference).identity.resource_id == "resource:alpha"

    with pytest.raises(ResourceCatalogError) as raised:
        catalog.get(
            ResourceReference(
                resource_id="resource:alpha",
                namespace="workspace:demo",
                version="2.0",
            )
        )

    assert raised.value.code is ResourceErrorCode.RESOURCE_NOT_FOUND


def test_catalogs_have_no_shared_or_global_state(
    dataset_type,
    descriptor_factory,
):
    first = ResourceCatalog(resource_types=(dataset_type,))
    second = ResourceCatalog(resource_types=(dataset_type,))
    first.register(descriptor_factory("resource:first"))

    assert len(first.list_descriptors()) == 1
    assert second.list_descriptors() == ()


def test_package_import_does_not_populate_a_catalog():
    import aegis_os.resources as resources

    assert not any(
        isinstance(value, ResourceCatalog)
        for value in vars(resources).values()
    )
    assert ResourceCatalog().list_descriptors() == ()
