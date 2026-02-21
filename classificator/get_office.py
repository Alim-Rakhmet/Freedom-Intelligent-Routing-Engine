from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from models.models import BusinessUnit

geolocator = Nominatim(user_agent="fire_routing_engine_v1")

def get_coordinates(address: str) -> tuple[float, float] | None:
    """Превращает текстовый адрес в кортеж (широта, долгота)."""
    try:
        # timeout нужен, чтобы скрипт не завис, если сервер OSM тупит
        location = geolocator.geocode(address, timeout=5)
        if location:
            return (location.latitude, location.longitude)
        return None
    except Exception as e:
        print(f"Ошибка геокодинга для '{address}': {e}")
        return None

def find_nearest_address(target_address: str, business_units: list[BusinessUnit]) -> BusinessUnit | None:
    """Ищет ближайший адрес из списка к целевому адресу"""
    print(f"Ищем координаты для клиента: {target_address}...")
    target_coords = get_coordinates(target_address)
    
    if not target_coords:
        print("Не удалось определить координаты целевого адреса.")
        return None

    closest_unit = None
    min_distance = float('inf') # Изначально минимальное расстояние равно бесконечности

    for unit in business_units:
        coords = get_coordinates(unit.address)
        if not coords:
            continue
            
        # Считаем расстояние в километрах
        distance = geodesic(target_coords, coords).kilometers
        print(f"Расстояние до '{unit.name}': {distance:.2f} км")
        
        # Если нашли вариант ближе, запоминаем его
        if distance < min_distance:
            min_distance = distance
            closest_unit = unit

    return closest_unit

# --- Тестируем ---
if __name__ == "__main__":
    client_address = "Казахстан, Өскемен, проспект Абая 50"
    
    # Теперь передаем список объектов BusinessUnit, как и требует функция
    offices = [
        BusinessUnit(name="Офис Усть-Каменогорск", address="Казахстан, Өскемен, Гоголя 20"),
        BusinessUnit(name="Офис Алматы", address="Казахстан, Алматы, улица Розыбакиева 247"),
        BusinessUnit(name="Офис Шымкент", address="Казахстан, Шымкент, площадь Аль-Фараби 1")
    ]
    
    nearest_unit = find_nearest_address(client_address, offices)
    
    if nearest_unit:
        print(f"\nСамый ближайший офис: {nearest_unit.name} по адресу {nearest_unit.address}")
    else:
        print("\nБлижайший офис не найден.")