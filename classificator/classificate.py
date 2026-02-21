import logging
from typing import List, Optional
from models.models import Ticket, Manager, BusinessUnit, Response

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
        manager=target_manager,
        business_unit=target_office,
        type=ai_data.get("type"),
        sentiment=ai_data.get("sentiment"),
        priority=ai_data.get("priority"),
        language=ai_data.get("language"),
        summary=ai_data.get("summary")
    )

if __name__ == "__main__":
    import uuid
    from datetime import date
    from models.models import Segment, Position, BusinessUnit, Manager, Ticket

    # --- 1. ИНИЦИАЛИЗАЦИЯ ТЕСТОВЫХ ДАННЫХ ---
    
    # Создаем офисы
    astana_office = BusinessUnit(
        name="Центральный филиал Астана", 
        address="Казахстан, Астана, проспект Мангилик Ел 53"
    )
    almaty_office = BusinessUnit(
        name="Филиал Алматы", 
        address="Казахстан, Алматы, улица Розыбакиева 247"
    )
    units = [astana_office, almaty_office]

    # Создаем менеджеров
    managers = [
        Manager(
            full_name="Бекзат Жумабаев",
            position=Position.CHIEF_SPEC,
            skills=["VIP", "KZ", "ENG"],
            business_unit=astana_office,
            current_load=0
        ),
        Manager(
            full_name="Иван Петров",
            position=Position.SPEC,
            skills=["RU"],
            business_unit=almaty_office,
            current_load=10
        )
    ]

    # --- 2. СОЗДАНИЕ ТЕСТОВЫХ КЕЙСОВ ---

    # Кейс 1: VIP клиент из Астаны с жалобой на казахском
    ticket_1 = Ticket(
        client_guid=uuid.uuid4(),
        gender="М",
        birth_date=date(1985, 5, 20),
        segment=Segment.VIP,
        description="Сәлеметсіз бе! Менің картам бұғатталып қалды, көмектесіңізші.",
        country="Казахстан",
        region="Акмолинская область",
        city="Астана",
        street="Конаева",
        house="12"
    )

    # Кейс 2: Обычный клиент из Алматы
    ticket_2 = Ticket(
        client_guid=uuid.uuid4(),
        gender="Ж",
        birth_date=date(1995, 10, 10),
        segment=Segment.MASS,
        description="Здравствуйте, как я могу открыть депозит в вашем приложении?",
        country="Казахстан",
        region="Алматинская область",
        city="Алматы",
        street="Толе Би",
        house="45"
    )

    # --- 3. ЗАПУСК ТЕСТИРОВАНИЯ ---
    
    test_tickets = [ticket_1, ticket_2]

    print("🚀 Запуск интеграционного теста FIRE...")
    print("="*50)

    for i, t in enumerate(test_tickets, 1):
        print(f"\nТест №{i}: Обработка обращения из города {t.city}")
        
        # Вызываем нашу главную функцию
        response = classificate(t, units, managers)

        if response:
            print(f"✅ УСПЕХ: Тикет распределен!")
            print(f"   Классификация ИИ: {response.type} (Тональность: {response.sentiment})")
            print(f"   Назначенный офис: {response.business_unit.name}")
            print(f"   Назначенный менеджер: {response.manager.full_name} ({response.manager.position})")
            print(f"   Краткое резюме: {response.summary}")
        else:
            print(f"❌ ОШИБКА: Не удалось обработать тикет.")
        
        print("-" * 30)

    print("\n🏁 Тестирование завершено.")