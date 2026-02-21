import os
import sys
import django

# Получаем абсолютный путь к корневой директории проекта
# Это позволит Python находить пакет 'datazavr', где расположены настройки Django
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Настройка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datazavr.core.settings')
django.setup()
