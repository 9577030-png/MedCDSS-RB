import re
import logging
from typing import List, Optional
from application.ports.parser_interface import ParserInterface
from domain.entities.parameter import Parameter
from domain.exceptions import ParsingError, InvalidParameterError
from .normalizer import ParameterNormalizer

logger = logging.getLogger(__name__)


class RegexParser(ParserInterface):
    """
    Токенизирующий парсер лабораторного текста.

    Поддерживает:
    - несколько параметров в одной строке через запятую/точку с запятой;
    - запятую как десятичный разделитель ("8,5" = 8.5), не путая её с разделителем
      между несколькими параметрами в одной строке;
    - референсные интервалы в скобках, вырезаются перед разбором
      ("Глюкоза: 8.0 ммоль/л (норма 3.9-6.1)");
    - составные имена параметров с цифрами ("T4 свободный", "HbA1c", "B12");
    - разные разделители между именем и значением: пробел, двоеточие, тире, "=".

    Ключевая идея: значение параметра - ПОСЛЕДНИЙ числовой токен в сегменте,
    а не первый - только так можно отличить значение от цифр внутри самого
    названия параметра (T4, B12, HbA1c и т.п.).
    """

    REFERENCE_RANGE = re.compile(r'\([^)]*\)')
    UNIT_PATTERN = re.compile(r'[A-Za-zА-Яа-я/%°]+(?:/[A-Za-zА-Яа-я]+)?')
    NUMBER_TOKEN = re.compile(r'-?\d+(?:[.,]\d+)?')
    NAME_TRAILING_SEP = re.compile(r'[:\-=\s]+$')

    def __init__(self):
        self.normalizer = ParameterNormalizer()
        logger.info("RegexParser (tokenizing) initialized")

    def parse(self, raw_text: str) -> List[Parameter]:
        logger.info("Parsing raw text")
        if not raw_text or not raw_text.strip():
            logger.warning("Empty raw text provided")
            raise ParsingError("Input text is empty")

        parameters = []
        lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
        logger.debug(f"Processing {len(lines)} lines")

        for line in lines:
            for segment in self._split_segments(line):
                param = self._parse_segment(segment)
                if param is not None:
                    parameters.append(param)

        if not parameters:
            raise ParsingError("No valid parameters could be extracted from input")

        logger.info(f"Parsed {len(parameters)} parameters")
        return parameters

    def _split_segments(self, line: str) -> List[str]:
        """
        Разбивает строку на сегменты вида "имя значение [единица]" по запятой
        или точке с запятой, НЕ разбивая внутри числа с запятой как десятичным
        разделителем (например "Глюкоза 8,5, HbA1c 7,2" -> два сегмента,
        а не четыре).
        """
        line = self.REFERENCE_RANGE.sub('', line)

        segments = []
        current = []
        n = len(line)
        for i, ch in enumerate(line):
            if ch in ',;':
                prev_is_digit = i > 0 and line[i - 1].isdigit()
                next_is_digit = i + 1 < n and line[i + 1].isdigit()
                if ch == ',' and prev_is_digit and next_is_digit:
                    current.append(ch)  # десятичный разделитель, не разделитель сегментов
                    continue
                seg = ''.join(current).strip()
                if seg:
                    segments.append(seg)
                current = []
                continue
            current.append(ch)
        seg = ''.join(current).strip()
        if seg:
            segments.append(seg)
        return segments

    def _parse_segment(self, segment: str) -> Optional[Parameter]:
        numbers = list(self.NUMBER_TOKEN.finditer(segment))
        if not numbers:
            logger.warning(f"No numeric value found in segment: {segment!r}")
            return None

        value_match = numbers[-1]
        value_str = value_match.group().replace(',', '.')
        try:
            value = float(value_str)
        except ValueError:
            logger.warning(f"Invalid numeric value in segment: {segment!r}")
            return None

        name_part = segment[:value_match.start()]
        name = self.NAME_TRAILING_SEP.sub('', name_part).strip()
        if not name:
            logger.warning(f"No parameter name found in segment: {segment!r}")
            return None

        rest = segment[value_match.end():].strip()
        unit_match = self.UNIT_PATTERN.match(rest)
        unit_str = unit_match.group() if unit_match else ''

        try:
            canonical_name, normalized_value, unit_obj = self.normalizer.normalize(name, value, unit_str)
            return Parameter(name=canonical_name, value=normalized_value, unit=unit_obj)
        except InvalidParameterError as e:
            logger.error(f"Skipping segment due to invalid parameter: {segment!r} - {e}")
            return None