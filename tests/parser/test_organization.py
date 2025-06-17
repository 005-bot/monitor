import pytest

from app.parser.organization import OrganizationParser, ResourceType


@pytest.fixture
def parser():
    return OrganizationParser()


@pytest.mark.parametrize(
    "input_string, expected_resource_type, expected_resource, expected_organization, expected_phones",
    [
        (
            "Горячее водоснабжение\nАО КТТК\nт. 264-18-62\nт. 214-93-51",
            ResourceType.HOT_WATER,
            "Горячее водоснабжение",
            "АО КТТК",
            ["264-18-62", "214-93-51"],
        ),
        (
            "Электроснабжение\nПАО Россети Сибирь\nт. 8-800-220-0-220",
            ResourceType.ELECTRICITY,
            "Электроснабжение",
            "ПАО Россети Сибирь",
            ["8-800-220-0-220"],
        ),
        (
            "Горячее водоснабжение с подающего трубопровода\nООО СибЭР (№ 980)\nт. 214-93-51",
            ResourceType.HOT_WATER,
            "Горячее водоснабжение с подающего трубопровода",
            "ООО СибЭР (№ 980)",
            ["214-93-51"],
        ),
        (
            "Холодное водоснабжение\nАО Красмаш\nт. 211-39-63",
            ResourceType.COLD_WATER,
            "Холодное водоснабжение",
            "АО Красмаш",
            ["211-39-63"],
        ),
        (
            "Холодное водоснабжение\nАО Пример\nт.123-45-67\nт. 987-65-43",
            ResourceType.COLD_WATER,
            "Холодное водоснабжение",
            "АО Пример",
            ["123-45-67", "987-65-43"],
        ),
        (
            "Холодное водоснабжение\nАО Красмаш",
            ResourceType.COLD_WATER,
            "Холодное водоснабжение",
            "АО Красмаш",
            [],
        ),
    ],
)
def test_organization_parsing(
    parser,
    input_string,
    expected_resource_type,
    expected_resource,
    expected_organization,
    expected_phones,
):
    result = parser.parse(input_string)

    assert result is not None
    assert result.resource_type == expected_resource_type
    assert result.resource == expected_resource
    assert result.organization == expected_organization
    assert result.phones == expected_phones


def test_invalid_input(parser):
    assert parser.parse("") is None
    assert parser.parse("Горячее водоснабжение") is None
