import logging
import re
import typing

from apis.models import OutageDetails, Reason, Street, WaterDelivery

if typing.TYPE_CHECKING:
    from address_parser import AddressParser

logger = logging.getLogger(__name__)


class OutageDetailsParser:
    def __init__(self, address_parser: "AddressParser"):
        self.address_parser = address_parser

    async def parse(self, input: str) -> OutageDetails | None:
        """Main method to parse all components of the input"""
        lines = [line.strip() for line in input.strip().split("\n") if line.strip()]

        if not lines:
            return None

        streets = []
        while (
            lines
            and "е - " not in lines[0]
            and (chunk := await self._parse_streets(lines.pop(0)))
        ):
            streets.extend(chunk)

        reason = None
        water_deliveries = None
        comments = None
        if len(lines) > 0:
            reason = self._parse_reason(lines[0])
        if len(lines) > 1:
            water_deliveries = self._parse_water_deliveries(lines[1])
            comments = "\n".join(lines[1:])

        if not streets:
            logger.warning("No streets found in input: %s", input)

        return OutageDetails(
            streets=streets,
            reason=reason,
            water_deliveries=water_deliveries,
            comments=comments,
        )

    async def _parse_streets(self, address_line: str) -> list[Street]:
        """Parse street addresses from the first line"""
        streets: list[Street] = []
        for street_part in address_line.split(";"):
            street_part = street_part.strip()
            if not street_part:
                continue

            street_name, numbers_str = self._split_street_and_numbers(street_part)
            if not street_name:
                continue

            match_name = await self.address_parser.normalize(street_name)
            if not match_name or match_name.confidence < 0.6:
                logger.warning(
                    "Rejected street match: '%s' (confidence: %.2f)",
                    street_name,
                    match_name.confidence if match_name else "None",
                )
            else:
                street_name = match_name.name

            buildings = self._process_building_numbers(numbers_str)

            streets.append(Street(name=street_name, buildings=buildings or None))

        if not streets:
            logger.warning("No valid streets found in line: %s", address_line)

        return streets

    @staticmethod
    def _split_street_and_numbers(
        street_part: str,
    ) -> tuple[str | None, str | None]:
        """Split street name from building numbers"""
        tokens = street_part.split()
        for i in range(1, len(tokens)):
            if tokens[i][0].isdigit() and tokens[i - 1][0].isalpha():
                return " ".join(tokens[:i]), " ".join(tokens[i:])
        return " ".join(tokens), None

    @staticmethod
    def _process_building_numbers(numbers_str: str | None) -> list[str] | None:
        """Clean and split building numbers"""
        if not numbers_str:
            return None

        numbers_str = re.sub(r"\(.+?\)", "", numbers_str)

        buildings = []
        for num_entry in re.split(r",\s*", numbers_str):
            cleaned = num_entry.split("(", 1)[0].strip()
            if not cleaned:
                logger.warning("Empty building number after cleaning: %s", num_entry)
                continue

            buildings.append(cleaned)

        if not buildings:
            logger.warning("No valid building numbers found in string: %s", numbers_str)

        return buildings

    @staticmethod
    def _parse_reason(line: str) -> Reason:
        """Parse reason line into Reason model"""
        if "-" not in line:
            logger.warning("Malformed reason line: %s", line)
            return Reason("неизвестное", line)

        reason_type, description = line.split("-", 1)
        return Reason(type=reason_type.strip(), description=description.strip())

    def _parse_water_deliveries(self, line: str) -> list[WaterDelivery] | None:
        """Parse water delivery information"""
        if not line.startswith("Подвоз воды: "):
            return None

        water_data: list[WaterDelivery] = []
        entries = line[len("Подвоз воды: ") :].strip().split(";")

        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue

            try:
                address_part, time_part = entry.split(" с ", 1)
                street, buildings = address_part.rsplit(" ", 1)
                if " до " not in time_part:
                    logger.warning("Malformed time format in water delivery: %s", entry)
                    continue
                time_start, time_end = time_part.split(" до ", 1)

                water_data.append(
                    WaterDelivery(
                        street=street.strip(),
                        buildings=buildings.strip(),
                        time_start=time_start.strip(),
                        time_end=time_end.strip(),
                    )
                )
            except ValueError as e:
                logger.warning("Malformed water delivery entry: %s (%s)", entry, e)
                continue

        if not water_data:
            logger.warning("No water delivery entries parsed from line: %s", line)

        return water_data or None
