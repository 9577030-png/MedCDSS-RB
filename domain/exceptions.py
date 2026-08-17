"""
Доменные исключения для медицинской системы поддержки принятия решений.
Все исключения наследуются от MedicalAIError, чтобы их можно было легко перехватывать.
"""

class MedicalAIError(Exception):
    """Базовое исключение для всех ошибок предметной области."""
    pass


# --- Ошибки валидации данных пациента ---

class InvalidPatientDataError(MedicalAIError):
    """Ошибка в данных пациента (например, отрицательный возраст, неверный пол)."""
    pass


# --- Ошибки парсинга ---

class ParsingError(MedicalAIError):
    """Ошибка при разборе входного текста (некорректный формат)."""
    pass


class InvalidParameterError(MedicalAIError):
    """Некорректный параметр (отрицательное значение, неизвестная единица и т.д.)."""
    pass


# --- Ошибки загрузки конфигураций ---

class ConfigurationError(MedicalAIError):
    """Ошибка в конфигурационных файлах (YAML)."""
    pass


class ThresholdNotFoundError(ConfigurationError):
    """Запрошенный порог не найден в глобальных настройках."""
    pass


class GuidelineLoadError(ConfigurationError):
    """Ошибка загрузки клинического руководства."""
    pass


# --- Ошибки выполнения анализа ---

class InferenceError(MedicalAIError):
    """Ошибка во время вывода (логика)."""
    pass


class RepositoryError(MedicalAIError):
    """Ошибка при работе с хранилищем."""
    pass


class RenderError(MedicalAIError):
    """Ошибка при рендеринге отчёта."""
    pass