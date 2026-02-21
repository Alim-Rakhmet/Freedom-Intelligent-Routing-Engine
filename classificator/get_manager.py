from typing import List, Optional
from models.models import *

round_robin_counter = 0

def get_manager(
    ticket: 'Ticket', 
    ticket_type: str, 
    language: str, 
    buisness_unit: 'BusinessUnit',
    office_managers: List['Manager']
) -> Optional['Manager']:
    global round_robin_counter
    
    eligible_managers = []
    
    for manager in office_managers:
        if manager.business_unit != buisness_unit:
            continue

        # Фильтр VIP/Priority
        if ticket.segment in [Segment.VIP, Segment.PRIORITY]:
            if "VIP" not in manager.skills:
                continue
                
        # Фильтр "Смена данных"
        if ticket_type == "Смена данных":
            if manager.position != Position.CHIEF_SPEC:
                continue
                
        # Фильтр по языку (если язык RU, то считаем, что его знают все)
        if language in ["KZ", "ENG"]:
            if language not in manager.skills:
                continue 
                
        eligible_managers.append(manager)
        
    if not eligible_managers:
        print("ВНИМАНИЕ: В данном офисе нет менеджеров, подходящих под условия тикета!")
        return None


    eligible_managers.sort(key=lambda m: m.current_load)
    
    # Берем топ-2 менеджеров с наименьшей нагрузкой
    top_candidates = eligible_managers[:2]
    
    # Используем остаток от деления, чтобы чередовать индексы 0 и 1 (поочередно)
    selected_index = round_robin_counter % len(top_candidates)
    selected_manager = top_candidates[selected_index]
    
    round_robin_counter += 1
    
    selected_manager.current_load += 1
    
    return selected_manager

# --- Тестируем логику ---
if __name__ == "__main__":
    from models.models import Ticket, Manager, Segment, Position, BusinessUnit
    import uuid
    from datetime import date
    
    # Создаем фейковые офисы
    test_unit = BusinessUnit(name="Офис Астана", address="...")
    wrong_unit = BusinessUnit(name="Офис Алматы", address="...")
    
    # Создаем команду менеджеров (один из них специально из другого офиса)
    team = [
        Manager("Алиса (Спец)", Position.SPEC, ["KZ"], test_unit, current_load=5),
        Manager("Бекзат (Глав)", Position.CHIEF_SPEC, ["VIP", "KZ"], test_unit, current_load=2),
        Manager("Виктор (Глав)", Position.CHIEF_SPEC, ["VIP", "ENG", "KZ"], test_unit, current_load=2),
        Manager("Гульназ (Ведущий)", Position.LEAD_SPEC, ["ENG"], test_unit, current_load=1),
        Manager("Левый чувак", Position.CHIEF_SPEC, ["VIP", "KZ"], wrong_unit, current_load=0) # Он подходит по скиллам, но из Алматы!
    ]
    
    test_ticket = Ticket(
        client_guid=uuid.uuid4(), gender="М", birth_date=date(1990,1,1),
        segment=Segment.VIP, description="...", country="KZ", region="", city="", street="", house=""
    )
    
    print("Тикет: Смена данных, VIP, KZ. Ищем в Офисе Астана.")
    for i in range(3):
        # ИСПРАВЛЕНИЕ 2: Передаем правильные названия аргументов и нужный офис
        manager = get_manager(
            ticket=test_ticket, 
            ticket_type="Смена данных", 
            language="KZ", 
            buisness_unit=test_unit, 
            office_managers=team
        )
        if manager:
            print(f"Итерация {i+1}: Назначен {manager.full_name} | Новая нагрузка: {manager.current_load}")
            