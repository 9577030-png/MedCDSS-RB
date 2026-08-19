import re
import logging
from typing import List
from application.ports.parser_interface import ParserInterface
from domain.entities.parameter import Parameter
from domain.exceptions import ParsingError, InvalidParameterError
from .normalizer import ParameterNormalizer

logger = logging.getLogger(__name__)

class RegexParser(ParserInterface):
    def __init__(self):
        self.normalizer = ParameterNormalizer()
        # Паттерн для имени с возможными цифрами в конце (без пробелов) – например, T4, B12
        self.pattern_with_digits = re.compile(
            r'(?P<name>[A-Za-zА-Яа-я_]+[0-9]+)\s*(?P<value>-?[\d.]+)\s*(?P<unit>[A-Za-z/%]+)?'
        )
        # Паттерн для имени с пробелами и без цифр – например, гликированный гемоглобин
        self.pattern_with_spaces = re.compile(
            r'(?P<name>[A-Za-zА-Яа-я_ ]+)\s*(?P<value>-?[\d.]+)\s*(?P<unit>[A-Za-z/%]+)?'
        )
        logger.info("RegexParser initialized with dual patterns")

    def parse(self, raw_text: str) -> List[Parameter]:
        logger.info("Parsing raw text")
        if not raw_text or not raw_text.strip():
            logger.warning("Empty raw text provided")
            raise ParsingError("Input text is empty")

        parameters = []
        lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
        logger.debug(f"Processing {len(lines)} lines")

        for line in lines:
            # Сначала пробуем паттерн с цифрами
            match = self.pattern_with_digits.search(line)
            if not match:
                # Если не сработал, пробуем паттерн с пробелами
                match = self.pattern_with_spaces.search(line)
            if not match:
                logger.warning(f"Could not parse line: {line}")
                continue

            name = match.group('name').strip()
            try:
                value = float(match.group('value'))
            except ValueError:
                logger.warning(f"Invalid numeric value in line: {line}")
                continue

            unit_str = match.group('unit') or ''

            try:
                canonical_name, normalized_value, unit_obj = self.normalizer.normalize(name, value, unit_str)
                param = Parameter(name=canonical_name, value=normalized_value, unit=unit_obj)
                parameters.append(param)
                logger.debug(f"Normalized: {param.name} = {param.value} {param.unit.name}")
            except InvalidParameterError as e:
                logger.error(f"Skipping line due to invalid parameter: {line} - {e}")
                continue

        if not parameters:
            raise ParsingError("No valid parameters could be extracted from input")

        logger.info(f"Parsed {len(parameters)} parameters")
        return parameters