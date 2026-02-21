# api/services.py
import json
from .models import Manager, BusinessUnit

# ЗАГЛУШКА ДЛЯ ИИ (Твои Data Science ребята должны вставить сюда реальный вызов LLM)
def analyze_text_with_llm(text: str) -> dict:
    """
    Тут ваша ML-модель или запрос к OpenAI/Claude.
    Должна возвращать словарь с ключами: type, sentiment, priority, language, summary
    """
    # ПРОСТЕЙШАЯ ЭВРИСТИКА ДЛЯ ТЕСТА (пока не подключили ML):
    text_lower = text.lower()
    
    issue_type = "Консультация"
    if "списан" in text_lower or "мошенник" in text_lower: issue_type = "Мошеннические действия"
    elif "смена" in text_lower or "изменить" in text_lower: issue_type = "Смена данных"
    elif "приложен" in text_lower or "ошибк" in text_lower: issue_type = "Неработоспособность приложения"
    
    sentiment = "negative" if any(w in text_lower for w in ["жалоба", "верните", "ужас", "суд"]) else "neutral"
    priority = 9 if issue_type == "Мошеннические действия" else 5
    lang = "kz" if "сәлеметсіз" in text_lower or "рақмет" in text_lower else "ru"
    if "hello" in text_lower: lang = "en"

    return {
        "type": issue_type,
        "sentiment": sentiment,
        "priority": priority,
        "language": lang,
        "summary": text[:100] + "..." # Краткая выжимка
    }


def find_best_manager(city: str, segment: str, issue_type: str, language: str) -> Manager:
    """
    Алгоритм балансировки из ТЗ (Round Robin + Фильтры)
    """
    managers = Manager.objects.all()

    # ФИЛЬТР 1: Город. Если нет в городе, ищем в Астане или Алматы
    local_managers = managers.filter(business_unit__name__icontains=city)
    if not local_managers.exists():
        local_managers = managers.filter(business_unit__name__in=['Астана', 'Алматы'])

    # ФИЛЬТР 2: VIP/Priority -> навык VIP
    if segment in ['VIP', 'Priority']:
        # В PostgreSQL JSONField можно фильтровать так (или просто через Python)
        local_managers = [m for m in local_managers if 'VIP' in m.skills]

    # ФИЛЬТР 3: Смена данных -> Главный спец
    if issue_type == 'Смена данных':
        local_managers = [m for m in local_managers if m.position == 'Главный специалист']

    # ФИЛЬТР 4: Язык (KZ/ENG)
    if language == 'kz':
        local_managers = [m for m in local_managers if 'KZ' in m.skills]
    elif language == 'en':
        local_managers = [m for m in local_managers if 'ENG' in m.skills]

    if not local_managers:
        # Fallback: отдаем самому свободному менеджеру в головных офисах, если никто не подошел
        return managers.filter(business_unit__name__in=['Астана', 'Алматы']).order_by('current_load').first()

    # БАЛАНСИРОВКА (Round Robin среди топ-2 с наименьшей нагрузкой)
    # Сортируем по нагрузке (возрастание)
    local_managers.sort(key=lambda m: m.current_load)
    
    # Берем топ-2 свободных
    top_2 = local_managers[:2]
    
    # Выбираем того, у кого нагрузка меньше (простейший Round Robin по нагрузке)
    selected_manager = top_2[0] 
    
    # Увеличиваем нагрузку, чтобы в следующий раз запрос улетел второму
    selected_manager.current_load += 1
    selected_manager.save()

    return selected_manager