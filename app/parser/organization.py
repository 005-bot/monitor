import logging
import re

from apis.models import OrganizationInfo, ResourceType

_PHONE_PREFIX_RE = re.compile(r"^\s*(?:т\.?\s*|тел\.?\s*|т:\s*)", re.IGNORECASE)

logger = logging.getLogger(__name__)


class OrganizationParser:
    """Parser for organization information from structured input strings"""

    def parse(self, input_str: str) -> OrganizationInfo | None:
        """Parse organization information from a multi-line input string"""
        lines = self._clean_input(input_str)

        if len(lines) < 2:
            logger.warning("Insufficient data in input: %s", input_str)
            return None

        resource = lines[0]
        organization = lines[1]
        phones = self._extract_phones(lines[2:])

        return OrganizationInfo(
            resource_type=self._get_resource_type(resource),
            resource=resource,
            organization=organization,
            phones=phones,
        )

    def _clean_input(self, input_str: str) -> list[str]:
        """Split input string into lines and strip whitespace"""
        return [line.strip() for line in input_str.split("\n") if line.strip()]

    def _get_resource_type(self, resource: str) -> ResourceType | None:
        for resource_type in ResourceType:
            if resource_type.value.lower() in resource.lower():
                return resource_type
        return None

    def _extract_phones(self, phone_lines: list[str]) -> list[str]:
        """Extract phone numbers from lines, removing service words like 'т.', 'тел.', or 'т:' prefixes"""
        return [
            cleaned
            for line in phone_lines
            if (cleaned := _PHONE_PREFIX_RE.sub("", line).strip())
        ]
