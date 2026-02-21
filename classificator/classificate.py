import logging
from typing import List, Optional
import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datazavr.core.settings')
django.setup()
from datazavr.api.models import Ticket, Manager, BusinessUnit, Response

from classificator.summary import analyze_ticket
from classificator.get_office import find_nearest_address
from classificator.get_manager import get_manager

def classificate(
    ticket: Ticket, 
    business_units: List[BusinessUnit], 
    all_managers: List[Manager]
) -> Optional[Response]:
    print(f"\n--- Начало обработки тикета {ticket.client_guid} ---")

    # 1. AI-анализ (NLP Модуль)
    # Получаем классификацию, тональность, приоритет и саммари
    ai_data = analyze_ticket(ticket.description)
    if not ai_data:
        logging.error(f"AI не смог проанализировать тикет {ticket.client_guid}")
        return None

    # 2. Географическая маршрутизация (Geo Модуль)
    # Находим лучший офис с учетом страны, города и нагрузки
    target_office = find_nearest_address(ticket, business_units, all_managers)
    if not target_office:
        logging.error(f"Не удалось найти подходящий офис для тикета {ticket.client_guid}")
        return None

    # 3. Назначение менеджера (Routing Модуль)
    # Ищем человека внутри выбранного офиса по хард-скиллам и Round Robin
    target_manager = get_manager(
        ticket=ticket,
        ticket_type=ai_data.get("ai_type", "Консультация"),
        language=ai_data.get("ai_language", "RU"),
        buisness_unit=target_office,
        office_managers=all_managers
    )

    if not target_manager:
        logging.warning(f"В офисе {target_office.name} нет подходящих менеджеров.")
        return None

    # 4. Сборка финального ответа
    # Мы используем данные из AI и найденные объекты
    return Response(
        ticket=ticket,
        assigned_manager=target_manager,
        issue_type=ai_data.get("type"),
        sentiment=ai_data.get("sentiment"),
        priority=ai_data.get("priority"),
        language=ai_data.get("language"),
        summary=ai_data.get("summary")
    )