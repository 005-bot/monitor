from address_parser import AddressParser
import pytest
import pytest_asyncio

from app.parser.outage_details import (
    OutageDetails,
    OutageDetailsParser,
    Reason,
    Street,
    WaterDelivery,
)


@pytest_asyncio.fixture
async def address_parser():
    async with AddressParser() as address_parser:
        yield address_parser


@pytest.fixture
def parser(address_parser):
    return OutageDetailsParser(address_parser)


@pytest.mark.parametrize(
    "input_string, expected_streets",
    [
        (
            "ул. Ленина 1, 2; пр. Мира 3, 4",
            [Street("улица Ленина", ["1", "2"]), Street("проспект Мира", ["3", "4"])],
        ),
        (
            "пр. Мира 5; ул. Советская 10, 11(литА)",
            [Street("проспект Мира", ["5"]), Street("Советская улица", ["10", "11"])],
        ),
        ("ул. Пушкина", [Street("улица Пушкина", None)]),
        ###
        (
            "Вильского 4а, 6а; Петра Словцова 2, 8; Гусарова 2, 13; Лесопарковая 11; Мирошниченко 2;",
            [
                Street("улица Вильского", ["4а", "6а"]),
                Street("улица Петра Словцова", ["2", "8"]),
                Street("улица Гусарова", ["2", "13"]),
                Street("Лесопарковая улица", ["11"]),
                Street("улица Мирошниченко", ["2"]),
            ],
        ),
        (
            "Мира 60 (Дом быта);",
            [Street("проспект Мира", ["60"])],
        ),
        (
            "Кольцевая 9 (4 подъезд, 5-й этаж);",
            [Street("Кольцевая улица", ["9"])],
        ),
        (
            "Красноярский рабочий 173а; Кольцевая 10а, 10б, 12, 12а (школа), 14, 16, 18;",
            [
                Street("проспект имени газеты Красноярский Рабочий", ["173а"]),
                Street(
                    "Кольцевая улица", ["10а", "10б", "12", "12а", "14", "16", "18"]
                ),
            ],
        ),
    ],
)
@pytest.mark.asyncio
async def test_street_parsing(parser, input_string, expected_streets):
    result = await parser._parse_streets(input_string)
    assert result == expected_streets


@pytest.mark.parametrize(
    "input_string, expected_reason",
    [
        (
            "аварийное - подстанция Радиотехническая фидер 126-01, повреждение кабельной линии	",
            Reason(
                "аварийное",
                "подстанция Радиотехническая фидер 126-01, повреждение кабельной линии",
            ),
        ),
        (
            "плановое - замена аварийного пожарного гидранта Сурикова 35",
            Reason("плановое", "замена аварийного пожарного гидранта Сурикова 35"),
        ),
    ],
)
def test_reason_parsing(parser, input_string, expected_reason):
    assert parser._parse_reason(input_string) == expected_reason


@pytest.mark.parametrize(
    "input_string, expected_deliveries",
    [
        (
            "Подвоз воды: ул. Ленина 1 с 10:00 до 18:00; ул. Мира 5 с 09:00 до 21:00",
            [
                WaterDelivery("ул. Ленина", "1", "10:00", "18:00"),
                WaterDelivery("ул. Мира", "5", "09:00", "21:00"),
            ],
        ),
        (
            "Подвоз воды: пр. Мира 10 с 08:00 до 20:00",
            [WaterDelivery("пр. Мира", "10", "08:00", "20:00")],
        ),
    ],
)
def test_water_delivery_parsing(parser, input_string, expected_deliveries):
    assert parser._parse_water_deliveries(input_string) == expected_deliveries


@pytest.mark.parametrize(
    "input_string, expected_result",
    [
        (
            "Красноярский рабочий 173а;",
            OutageDetails(
                streets=[
                    Street("проспект имени газеты Красноярский Рабочий", ["173а"])
                ],
            ),
        ),
        (
            "Вильского 4а, 6а; Петра Словцова 2, 8; Гусарова 2, 13; Лесопарковая 11; Мирошниченко 2;\nаварийное - подстанция Радиотехническая фидер 126-01, повреждение кабельной линии",
            OutageDetails(
                streets=[
                    Street("улица Вильского", ["4а", "6а"]),
                    Street("улица Петра Словцова", ["2", "8"]),
                    Street("улица Гусарова", ["2", "13"]),
                    Street("Лесопарковая улица", ["11"]),
                    Street("улица Мирошниченко", ["2"]),
                ],
                reason=Reason(
                    "аварийное",
                    "подстанция Радиотехническая фидер 126-01, повреждение кабельной линии",
                ),
            ),
        ),
        (
            "Пировская 3-65, 2-76; Курейская, 6-20, 1-9;  Каратузский 32а, 34а, 36, 36а, 36б, 38, 40, 40/1, 40а, 42, 44, 46, 48, 48/1, 13а ст.1, 13а ст.2, 15а, 15-41; Бийхемская 2-18; 1-19;  Назаровская 1-63, 2-84;\nаварийное - устранение утечки в водопроводном колодце Каратузский 15",
            OutageDetails(
                streets=[
                    Street(
                        "Пировская улица",
                        ["3-65", "2-76"],
                    ),
                    Street(
                        "Курейская улица",
                        ["6-20", "1-9"],
                    ),
                    Street(
                        "Каратузский переулок",
                        [
                            "32а",
                            "34а",
                            "36",
                            "36а",
                            "36б",
                            "38",
                            "40",
                            "40/1",
                            "40а",
                            "42",
                            "44",
                            "46",
                            "48",
                            "48/1",
                            "13а ст.1",
                            "13а ст.2",
                            "15а",
                            "15-41",
                        ],
                    ),
                    Street(
                        "Бийхемская улица",
                        ["2-18"],
                    ),
                    Street(
                        "Назаровская улица",
                        ["1-63", "2-84"],
                    ),
                ],
                reason=Reason(
                    "аварийное",
                    "устранение утечки в водопроводном колодце Каратузский 15",
                ),
            ),
        ),
        (
            "Красноярский рабочий 173а;\nКольцевая 10а, 10б, 12, 12а (школа), 14, 16, 18;\nплановое - переврезка подающего трубопровода на постоянную схему",
            OutageDetails(
                streets=[
                    Street(
                        "проспект имени газеты Красноярский Рабочий",
                        ["173а"],
                    ),
                    Street(
                        "Кольцевая улица",
                        ["10а", "10б", "12", "12а", "14", "16", "18"],
                    ),
                ],
                reason=Reason(
                    "плановое",
                    "переврезка подающего трубопровода на постоянную схему",
                ),
            ),
        ),
        (
            "Мате Залки; Космонавтов; Харламова; Тельмана; Джамбульская; Новгородская; Металлургов;\nаварийное - причина выясняется",
            OutageDetails(
                streets=[
                    Street("улица Мате Залки", None),
                    Street("улица Космонавтов", None),
                    Street("улица Харламова", None),
                    Street("улица Тельмана", None),
                    Street("Джамбульская улица", None),
                    Street("Новгородская улица", None),
                    Street("проспект Металлургов", None),
                ],
                reason=Reason("аварийное", "причина выясняется"),
            ),
        ),
    ],
)
@pytest.mark.asyncio
async def test_full_parsing(parser, input_string, expected_result):
    result = await parser.parse(input_string)

    assert result == expected_result


@pytest.mark.asyncio
async def test_empty_input(parser):
    assert await parser.parse("") is None


@pytest.mark.asyncio
async def test_partial_input(parser):
    input_string = "ул. Ленина 1, 2"
    result = await parser.parse(input_string)
    assert isinstance(result, OutageDetails)
    assert len(result.streets) == 1
    assert result.reason is None
    assert result.water_deliveries is None


# def test_malformed_input(parser):
#     input_string = "Invalid format"
#     result = parser.parse(input_string)
#     assert result is None
