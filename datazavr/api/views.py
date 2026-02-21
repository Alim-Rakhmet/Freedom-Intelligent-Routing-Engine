import csv
import os
import concurrent.futures
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response as DRFResponse
from .models import Ticket, Response, Manager, BusinessUnit
from .serializers import BackendResponseSerializer

# Грязный хак для локального manage.py
import sys
# views.py -> api -> datazavr -> Freedom-Intelligent-Routing-Engine
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Импортируем вашу внешнюю логику
from classificator.classificate import classificate


class ProcessedTicketsAPIView(APIView):
    def get(self, request):
        data_dir = os.path.join(settings.BASE_DIR, 'data')
        bu_file = os.path.join(data_dir, 'business_units.csv')
        mgr_file = os.path.join(data_dir, 'managers.csv')
        tkt_file = os.path.join(data_dir, 'tickets.csv')

        if not all(os.path.exists(f) for f in [bu_file, mgr_file, tkt_file]):
            return DRFResponse({"error": "Один из CSV файлов не найден в папке datazavr/data/"}, status=404)

        # 1. ОЧИСТКА ДО ВЕДРА
        Response.objects.all().delete()
        Ticket.objects.all().delete()
        Manager.objects.all().delete()
        BusinessUnit.objects.all().delete()

        # 2. ЗАГРУЗКА БИЗНЕС-ЮНИТОВ
        with open(bu_file, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                BusinessUnit.objects.create(
                    name=row.get('Офис', '').strip(),
                    address=row.get('Адрес', '').strip()
                )

        # 3. ЗАГРУЗКА МЕНЕДЖЕРОВ
        with open(mgr_file, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                office_name = row.get('Офис', '').strip()
                bu = BusinessUnit.objects.filter(name__icontains=office_name).first()
                if bu:
                    skills_raw = row.get('Навыки', '')
                    skills_list = [s.strip() for s in skills_raw.split(',')] if skills_raw else []
                    Manager.objects.create(
                        full_name=row.get('ФИО', '').strip(),
                        position=row.get('Должность', '').strip(),
                        business_unit=bu,
                        skills=skills_list,
                        current_load=int(row.get('Количество обращений в работе', '0'))
                    )

        # 4. СОЗДАНИЕ ТИКЕТОВ В БАЗЕ (подготовка к AI)
        tickets_to_process = []
        with open(tkt_file, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                birth_date_raw = row.get('Дата рождения', '')
                clean_date = birth_date_raw.split(' ')[0] if birth_date_raw else "2000-01-01"

                ticket = Ticket.objects.create(
                    client_guid=row.get('GUID клиента', ''),
                    gender=row.get('Пол клиента', ''),
                    birth_date=clean_date,
                    segment=row.get('Сегмент клиента', ''),
                    description=row.get('Описание', ''),
                    country=row.get('Страна', ''),
                    region=row.get('Область', ''),
                    city=row.get('Населённый пункт', ''),
                    street=row.get('Улица', ''),
                    house=row.get('Дом', '')
                )
                tickets_to_process.append(ticket)

        # 5. АСИНХРОННАЯ ОБРАБОТКА (ThreadPoolExecutor для ИИ)
        all_managers = list(Manager.objects.all())
        all_units = list(BusinessUnit.objects.all())
        completed_responses = []

        def process_single_ticket(t):
            # Передаем объекты в ваш существующий маршрутизатор ИИ
            # Если classificate() вернет успешный объект Response, он уже будет создан через конструктор Python
            # Нам нужно будет его только сохранить в БД.
            return classificate(t, all_units, all_managers)

        # Запускаем 5 потоков одновременно
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Запускаем задачи
            future_to_ticket = {executor.submit(process_single_ticket, t): t for t in tickets_to_process}
            
            for future in concurrent.futures.as_completed(future_to_ticket):
                try:
                    res_obj = future.result()
                    if res_obj:
                        res_obj.save() # Сохраняем в БД то, что вернул classificate
                        completed_responses.append(res_obj)
                except Exception as exc:
                    print(f"Ошибка при обработке тикета {future_to_ticket[future].client_guid}: {exc}")

        # Сортируем для красоты и сериализуем
        completed_responses.sort(key=lambda x: x.created_at, reverse=True)
        serializer = BackendResponseSerializer(completed_responses, many=True)
        return DRFResponse(serializer.data)