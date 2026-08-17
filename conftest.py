import sys
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы все импорты работали
sys.path.insert(0, str(Path(__file__).parent))