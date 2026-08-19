"""
Доменные исключения для медицинской системы поддержки принятия решений.
Все исключения наследуются от MedicalAIError.
"""

class MedicalAIError(Exception):
    """Базовое исключение для всех ошибок предметной области."""
    pass


# --- Ошибки валидации данных пациента ---

class InvalidPatientDataError(MedicalAIError):
    """Ошибка в данных пациента (отрицательный возраст, неверный пол)."""
    pass


class InvalidParameterError(MedicalAIError):
    """Некорректный лабораторный параметр (отрицательное значение, неизвестная единица)."""
    pass


# --- Ошибки парсинга ---

class ParsingError(MedicalAIError):
    """Ошибка при разборе входного текста (некорректный формат)."""
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
    """Ошибка во время логического вывода."""
    pass


class ConflictResolutionError(MedicalAIError):
    """Ошибка при разрешении конфликтов между находками."""
    pass


class RepositoryError(MedicalAIError):
    """Ошибка при работе с репозиторием (БД, файлы)."""
    pass


class VersionNotFoundError(RepositoryError):
    """Запрошенная версия правила не найдена."""
    pass


class CacheError(MedicalAIError):
    """Ошибка при работе с кэшем."""
    pass


class RenderError(MedicalAIError):
    """Ошибка при рендеринге отчёта."""
    pass