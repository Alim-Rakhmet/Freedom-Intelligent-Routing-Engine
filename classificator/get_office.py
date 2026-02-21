import ssl
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from models.models import BusinessUnit, Manager, Ticket

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
    city_units = [u for u in business_units if city_name.lower() in u.address.lower()]
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
        city_offices = [u for u in business_units if target_city in u.address.lower()]
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
    
if __name__ == "__main__":
    import uuid
    from datetime import date
    from models.models import Segment, Position

    # --- ПОДГОТОВКА ДАННЫХ ---
    
    # 1. Офисы
    bu_astana = BusinessUnit(name="Астана Сити", address="Казахстан, Астана, Кунаева 1")
    bu_almaty_1 = BusinessUnit(name="Алматы Орбита", address="Казахстан, Алматы, Мустафина 5")
    bu_almaty_2 = BusinessUnit(name="Алматы Центр", address="Казахстан, Алматы, Абая 10")
    bu_shymkent = BusinessUnit(name="Шымкент Офис", address="Казахстан, Шымкент, Момышулы 12")
    
    all_units = [bu_astana, bu_almaty_1, bu_almaty_2, bu_shymkent]

    # 2. Менеджеры (для проверки нагрузки)
    # Сделаем Астану перегруженной (60), а Алмату посвободнее (10+5=15)
    all_managers = [
        Manager("Асет", Position.SPEC, [], bu_astana, current_load=60),
        Manager("Мария", Position.SPEC, [], bu_almaty_1, current_load=10),
        Manager("Иван", Position.SPEC, [], bu_almaty_2, current_load=5),
        Manager("Дулат", Position.SPEC, [], bu_shymkent, current_load=0)
    ]

    # Вспомогательная функция для создания тикета
    def create_test_ticket(city, country="Казахстан", street="Абая", house="1"):
        return Ticket(
            client_guid=uuid.uuid4(), gender="М", birth_date=date(1990, 1, 1),
            segment=Segment.MASS, description="Тест",
            country=country, region="...", city=city, street=street, house=house
        )

    print("\n🚀 ЗАПУСК ТЕСТОВ МАРШРУТИЗАЦИИ\n" + "="*50)

    # ТЕСТ 1: Прямое совпадение города (Шымкент - 1 офис)
    print("\nТЕСТ 1: Город с одним офисом (Шымкент)")
    ticket_shym = create_test_ticket("Шымкент")
    res1 = find_nearest_address(ticket_shym, all_units, all_managers)
    print(f"Результат: {res1.name if res1 else 'None'}")

    # ТЕСТ 2: Несколько офисов в городе (Алматы - 2 офиса)
    # В этом тесте будет дергаться геокодер (Nominatim)
    print("\nТЕСТ 2: Несколько офисов (Алматы). Ожидаем запуск геокодера...")
    ticket_almaty = create_test_ticket("Алматы", street="Мустафина", house="5")
    res2 = find_nearest_address(ticket_almaty, all_units, all_managers)
    print(f"Результат: {res2.name if res2 else 'None'}")

    # ТЕСТ 3: Зарубежный адрес (Турция)
    # Должен сработать Fallback и выбрать Алматы, так как там нагрузка (15) меньше Астаны (60)
    print("\nТЕСТ 3: Зарубежный клиент (Турция)")
    ticket_turkey = create_test_ticket("Стамбул", country="Турция")
    res3 = find_nearest_address(ticket_turkey, all_units, all_managers)
    print(f"Результат (ожидаем Алматы): {res3.name if res3 else 'None'}")

    # ТЕСТ 4: Город в КЗ, где нет офисов (Павлодар)
    # Должен сработать Fallback по нагрузке
    print("\nТЕСТ 4: Город в КЗ без офисов (Павлодар)")
    ticket_pavlodar = create_test_ticket("Павлодар")
    res4 = find_nearest_address(ticket_pavlodar, all_units, all_managers)
    print(f"Результат (ожидаем Алматы): {res4.name if res4 else 'None'}")

    # ТЕСТ 5: Ошибка геокодинга (Несуществующий адрес)
    # Если геокодер не найдет "Планета Марс", должен сработать Fallback
    print("\nТЕСТ 5: Несуществующий адрес в Алматы (Проверка Fallback)")
    ticket_mars = create_test_ticket("Алматы", street="Улица Несуществующая", house="9999")
    res5 = find_nearest_address(ticket_mars, all_units, all_managers)
    print(f"Результат: {res5.name if res5 else 'None'}")