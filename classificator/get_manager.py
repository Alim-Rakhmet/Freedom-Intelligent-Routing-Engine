from typing import List, Optional
import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datazavr.core.settings')
django.setup()

from datazavr.api.models import Ticket, Manager, BusinessUnit

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