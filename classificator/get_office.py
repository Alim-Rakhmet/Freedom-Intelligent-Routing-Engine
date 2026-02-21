import ssl
import os, sys
from geopy.geocoders import Nominatim

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
django_root = os.path.join(project_root, 'datazavr')
if django_root not in sys.path:
    sys.path.insert(0, django_root)

# Инициализируем Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

from geopy.distance import geodesic
from api.models import BusinessUnit, Manager, Ticket

geolocator = Nominatim(user_agent="fire_routing_engine_v3")

def get_coordinates(address: str) -> tuple[float, float] | None:
    try:
        location = geolocator.geocode(address, timeout=5)
        if location:
            return (location.latitude, location.longitude)
        return None
    except Exception as e:
        print(f"Ошибка геокодинга для '{address}': {e}")
        return None

def get_office_load(office: BusinessUnit, all_managers: list[Manager]) -> int:
    """Считает суммарную нагрузку всех менеджеров в конкретном офисе."""
    return sum(m.current_load for m in all_managers if m.business_unit == office)

def get_city_total_load(city_name: str, business_units: list[BusinessUnit], all_managers: list[Manager]) -> int:
    """Считает общую нагрузку по всем офисам конкретного города (Астана или Алматы)."""
    city_units = [u for u in business_units if city_name.lower() in u.name.lower() or city_name.lower() in u.address.lower()]
    return sum(get_office_load(u, all_managers) for u in city_units)

def find_nearest_address(
    ticket: Ticket, 
    business_units: list[BusinessUnit], 
    all_managers: list[Manager]
) -> BusinessUnit:
    
    def fallback_logic() -> BusinessUnit:
        print("💡 Применяем Fallback: сравниваем нагрузку Астаны и Алматы...")
        astana_load = get_city_total_load("астана", business_units, all_managers)
        almaty_load = get_city_total_load("алматы", business_units, all_managers)
        
        target_city = "астана" if astana_load <= almaty_load else "алматы"
        print(f"   Нагрузка: Астана({astana_load}) vs Алматы({almaty_load}). Выбрана {target_city.title()}.")
        
        # Берем любой офис из выбранного города 
        city_offices = [u for u in business_units if target_city in u.name.lower() or target_city in u.address.lower()]
        
        # Защита от пустого списка
        if not city_offices:
            print(f"⚠️ Офисы со словом {target_city} не найдены! Выбираем любой доступный офис.")
            return min(business_units, key=lambda u: get_office_load(u, all_managers))
            
        return min(city_offices, key=lambda u: get_office_load(u, all_managers))

    # 1. ПРОВЕРКА СТРАНЫ
    if ticket.country.lower() not in ["казахстан", "kazakhstan", "kz"]:
        print(f"🌍 Клиент из-за рубежа ({ticket.country}).")
        return fallback_logic()

    # 2. ПРОВЕРКА ПО ГОРОДУ
    city_matches = [u for u in business_units if ticket.city.lower() in u.address.lower()]
    
    if len(city_matches) == 1:
        print(f"⚡ Прямое совпадение! В городе {ticket.city} найден один офис. Назначаем.")
        return city_matches[0]
    
    # Определяем круг поиска для координат
    # Если в городе несколько офисов, ищем среди них. Если 0 — ищем по астане/алматы.
    if len(city_matches) > 1:
        print(f"🔍 В городе {ticket.city} несколько офисов ({len(city_matches)}). Уточняем по координатам...")
        # 3. ПРОВЕРКА ПО КООРДИНАТАМ
        full_address = f"{ticket.country}, {ticket.city}, {ticket.street}, {ticket.house}"
        target_coords = get_coordinates(full_address) # Функция из предыдущих шагов
    
        if not target_coords:
            print(f"❌ Координаты для адреса '{full_address}' не найдены.")
            return fallback_logic()

        # Ищем ближайший среди пула
        closest_unit = None
        min_distance = float('inf')

        for unit in city_matches:
            unit_coords = get_coordinates(unit.address)
            if not unit_coords: continue

            dist = geodesic(target_coords, unit_coords).kilometers
            if dist < min_distance:
                min_distance = dist
                closest_unit = unit

        return closest_unit if closest_unit else fallback_logic()
    else:
        print(f"📍 В городе {ticket.city} офисов нет. Ищем ближайший в других городах...")
        return fallback_logic()