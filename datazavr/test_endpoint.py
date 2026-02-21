import requests
import time

start = time.time()
print("Отправляю запрос на GET http://127.0.0.1:8000/api/tickets/")
try:
    response = requests.get('http://127.0.0.1:8000/api/tickets/')
    print(f"Статус: {response.status_code}")
    print(f"Время выполнения: {time.time() - start:.2f} сек")
    json_data = response.json()
    if isinstance(json_data, list):
        print(f"Получено тикетов: {len(json_data)}")
    else:
        print("Ошибка:", json_data)
except Exception as e:
    print(f"Ошибка соединения: {e}")
