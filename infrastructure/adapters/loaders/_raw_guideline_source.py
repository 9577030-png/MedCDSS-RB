import os
import yaml
from typing import List, Dict, Any
from pathlib import Path

class RawGuidelineSource:
    """Читает все YAML-файлы из knowledge/guidelines/ и возвращает сырые данные."""

    def __init__(self, base_path: str = "knowledge/guidelines"):
        self.base_path = Path(base_path)

    def load_all(self) -> List[Dict[str, Any]]:
        result = []
        if not self.base_path.exists():
            return result

        for yaml_file in self.base_path.rglob("*.yaml"):
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    # Убедимся, что у каждого правила есть id (имя файла без расширения)
                    data["id"] = data.get("id", yaml_file.stem)
                    result.append(data)
        return result