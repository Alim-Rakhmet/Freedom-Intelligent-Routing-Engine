from typing import List, Optional
import os, sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
django_root = os.path.join(project_root, 'datazavr')
if django_root not in sys.path:
    sys.path.insert(0, django_root)

# Инициализируем Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

from api.models import Ticket, Manager, BusinessUnit

# Record counter per office to ensure round-robin within the office
office_round_robin_counters = {}

def get_manager(
    ticket: 'Ticket', 
    ticket_type: str, 
    language: str, 
    buisness_unit: 'BusinessUnit',
    office_managers: List['Manager']
) -> Optional['Manager']:
    
    eligible_managers = []
    
    for manager in office_managers:
        if manager.business_unit != buisness_unit:
            continue

        # Фильтр VIP/Priority
        if ticket.segment in ["VIP", "Priority"]:
            if "VIP" not in manager.skills:
                continue
                
        # Фильтр "Смена данных"
        if ticket_type == "Смена данных":
            if manager.position != "Глав спец":
                continue
                
        # Фильтр по языку (если язык RU, то считаем, что его знают все)
        if language in ["KZ", "ENG"]:
            if language not in manager.skills:
                continue 
                
        eligible_managers.append(manager)
        
    # ЕСЛИ В ЭТОМ ОФИСЕ НИКТО НЕ НАЙДЕН - ВЫРУБАЕМ ПРИСТЯЖКУ К ОФИСУ И ИЩЕМ ПО ВСЕЙ КОМПАНИИ
    if not eligible_managers:
        print(f"⚠️ В офисе {buisness_unit.name} нет менеджера под тикет '{ticket_type}' с языком '{language}'. Ищем по всем офисам...")
        
        for manager in office_managers:
            # Фильтр VIP/Priority
            if ticket.segment in ["VIP", "Priority"]:
                if "VIP" not in manager.skills:
                    continue
                    
            # Фильтр "Смена данных"
            if ticket_type == "Смена данных":
                if manager.position != "Глав спец":
                    continue
                    
            # Фильтр по языку
            if language in ["KZ", "ENG"]:
                if language not in manager.skills:
                    continue 
                    
            eligible_managers.append(manager)
            
        if not eligible_managers:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Ни один менеджер в компании не подходит под этот тикет!")
            return None


    eligible_managers.sort(key=lambda m: m.current_load)
    
    # Берем топ-2 менеджеров с наименьшей нагрузкой
    top_candidates = eligible_managers[:2]
    
    # Initialize counter for this office if it doesn't exist (using a generic "all" ID for fallback cases if managers are from different offices)
    # Using the top candidate's actual office for the counter to be safe
    office_id = top_candidates[0].business_unit.id if top_candidates else buisness_unit.id
    
    if office_id not in office_round_robin_counters:
        office_round_robin_counters[office_id] = 0
        
    # Используем остаток от деления, чтобы чередовать индексы 0 и 1 (поочередно)
    selected_index = office_round_robin_counters[office_id] % len(top_candidates)
    selected_manager = top_candidates[selected_index]
    
    office_round_robin_counters[office_id] += 1
    
    selected_manager.current_load += 1
    
    return selected_manager