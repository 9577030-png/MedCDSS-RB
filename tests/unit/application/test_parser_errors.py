import pytest
from infrastructure.adapters.parsers.regex_parser import RegexParser
from domain.exceptions import ParsingError

def test_parser_handles_empty_text():
    parser = RegexParser()
    with pytest.raises(ParsingError, match="empty"):
        parser.parse("")

def test_parser_handles_invalid_lines_gracefully():
    parser = RegexParser()
    text = """Hb 120 g/L
    Invalid line without value
    Ferritin 30 ug/L
    """
    params = parser.parse(text)
    assert len(params) == 2
    names = [p.name for p in params]
    # Теперь каноническое имя 'hb', а не 'hemoglobin'
    assert "hb" in names
    assert "ferritin" in names

def test_parser_handles_negative_values():
    parser = RegexParser()
    text = "Hb -10 g/L"
    with pytest.raises(ParsingError, match="No valid parameters"):
        parser.parse(text)