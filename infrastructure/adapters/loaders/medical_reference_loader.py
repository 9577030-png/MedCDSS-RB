import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class MedicalReferenceLoader:
    """
    Загрузчик референсных интерпретаций для лабораторных показателей.
    Данные могут быть загружены из YAML или словаря.
    """

    def __init__(self, config_path: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
        """
        Инициализация загрузчика.
        :param config_path: путь к YAML-файлу с референсными данными (опционально)
        :param data: словарь с данными (если не указан путь)
        """
        self._references: Dict[str, Any] = {}
        if config_path:
            self._load_from_yaml(config_path)
        elif data:
            self._references = data
        else:
            logger.warning("MedicalReferenceLoader initialized without data")

        # Кэш для быстрого доступа (имя параметра -> список диапазонов)
        self._param_cache: Dict[str, List[Dict]] = {}
        self._build_cache()

        logger.info(f"MedicalReferenceLoader initialized: {len(self._references)} parameters")

    def _load_from_yaml(self, path: str) -> None:
        """Загрузка данных из YAML-файла."""
        try:
            import yaml
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            if data and isinstance(data, dict):
                self._references = data.get('parameters', {})
            else:
                logger.warning(f"Invalid YAML structure in {path}")
        except Exception as e:
            logger.error(f"Failed to load medical references from {path}: {e}")
            self._references = {}

    def _build_cache(self) -> None:
        """Строит кэш для быстрого поиска по имени параметра."""
        for param_name, config in self._references.items():
            intervals = config.get('intervals', [])
            if intervals:
                self._param_cache[param_name] = intervals

    def get_interpretation(self, param_name: str, value: Any,
                           gender: Optional[str] = None,
                           age: Optional[float] = None) -> Dict[str, Any]:
        """
        Получить интерпретацию значения параметра с учётом пола и возраста.
        :param param_name: каноническое имя параметра
        :param value: числовое значение (может быть None)
        :param gender: 'male' или 'female' (опционально)
        :param age: возраст в годах (опционально)
        :return: словарь с интерпретацией (ключи: status, comment, range и т.п.)
        """
        # ★★★ ИСПРАВЛЕНИЕ: если значение отсутствует, сразу возвращаем пустой результат ★★★
        if value is None:
            logger.debug(f"Value is None for parameter {param_name}, skipping interpretation")
            return {}

        intervals = self._param_cache.get(param_name)
        if not intervals:
            logger.debug(f"No intervals found for parameter {param_name}")
            return {}

        # Приводим value к числу, если это возможно
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            logger.warning(f"Value {value} for {param_name} is not numeric, skipping interpretation")
            return {}

        # Фильтруем интервалы по полу и возрасту (если указаны)
        applicable = []
        for interval in intervals:
            # Проверка пола
            if 'gender' in interval and interval['gender']:
                if gender and interval['gender'].lower() != gender.lower():
                    continue
            # Проверка возраста (если задан диапазон)
            if 'age_min' in interval and age is not None:
                if age < interval['age_min']:
                    continue
            if 'age_max' in interval and age is not None:
                if age > interval['age_max']:
                    continue
            applicable.append(interval)

        # Сортируем по приоритету: сначала точные совпадения (более узкие интервалы)
        # Здесь можно применить эвристику, но для простоты перебираем все
        for interval in applicable:
            min_val = interval.get('min')
            max_val = interval.get('max')

            # ★★★ Защита от None в min/max ★★★
            if min_val is not None and numeric_value < min_val:
                continue
            if max_val is not None and numeric_value > max_val:
                continue

            # Нашли подходящий интервал
            return {
                'status': interval.get('status', 'normal'),
                'comment': interval.get('comment', ''),
                'range': f"{min_val or '…'} – {max_val or '…'}",
                'risk_level': interval.get('risk', 'LOW'),
                'recommendations': interval.get('recommendations', []),
            }

        # Если ни один интервал не подошёл (выход за пределы всех диапазонов)
        # Можно попытаться определить крайний случай, но для простоты возвращаем общее
        return {
            'status': 'unknown',
            'comment': f'Значение {numeric_value} вне заданных референсных интервалов для {param_name}',
            'range': 'не определено',
            'risk_level': 'MEDIUM',
            'recommendations': ['Требуется уточнение референсных значений']
        }

    def get_all_parameters(self) -> List[str]:
        """Возвращает список всех доступных имён параметров."""
        return list(self._references.keys())

    def get_parameter_config(self, param_name: str) -> Optional[Dict]:
        """Возвращает полную конфигурацию параметра."""
        return self._references.get(param_name)