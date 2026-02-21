import csv
import os
import time
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
        
        # 1. ЗАГРУЗКА СПРАВОЧНИКОВ, ЕСЛИ ИХ НЕТ В БД
        if not BusinessUnit.objects.exists() or not Manager.objects.exists():
            bu_file = os.path.join(data_dir, 'business_units.csv')
            mgr_file = os.path.join(data_dir, 'managers.csv')
            
            if os.path.exists(bu_file):
                with open(bu_file, encoding='utf-8-sig') as f:
                    for row in csv.DictReader(f):
                        BusinessUnit.objects.get_or_create(
                            name=row.get('Офис', '').strip(),
                            defaults={'address': row.get('Адрес', '').strip()}
                        )

            if os.path.exists(mgr_file):
                with open(mgr_file, encoding='utf-8-sig') as f:
                    for row in csv.DictReader(f):
                        office_name = row.get('Офис', '').strip()
                        bu = BusinessUnit.objects.filter(name__icontains=office_name).first()
                        if bu:
                            skills_raw = row.get('Навыки', '')
                            skills_list = [s.strip() for s in skills_raw.split(',')] if skills_raw else []
                            Manager.objects.get_or_create(
                                full_name=row.get('ФИО', '').strip(),
                                defaults={
                                    'position': row.get('Должность ', row.get('Должность', '')).strip(),
                                    'skills': skills_list,
                                    'business_unit': bu,
                                    'current_load': int(row.get('Количество обращений в работе', '0') or 0)
                                }
                            )

        # 2. ЗАГРУЗКА ТИКЕТОВ, ЕСЛИ ИХ НЕТ В БД
        if not Ticket.objects.exists():
            tkt_file = os.path.join(data_dir, 'tickets.csv')
            if os.path.exists(tkt_file):
                with open(tkt_file, encoding='utf-8-sig') as f:
                    for row in csv.DictReader(f):
                        birth_date_raw = row.get('Дата рождения', '')
                        clean_date = birth_date_raw.split(' ')[0] if birth_date_raw else "2000-01-01"

                        Ticket.objects.create(
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

        # 3. ПОЛУЧАЕМ ОДИН НЕОБРАБОТАННЫЙ ТИКЕТ
        ticket = Ticket.objects.filter(ai_response__isnull=True).first()
        
        if not ticket:
            return DRFResponse({"message": "Все тикеты уже обработаны!"}, status=200)

        # 4. ОБРАБАТЫВАЕМ ТОЛЬКО ЭТОТ ТИКЕТ
        all_managers = list(Manager.objects.all())
        all_units = list(BusinessUnit.objects.all())
        
        try:
            res_obj = classificate(ticket, all_units, all_managers)
            if res_obj:
                res_obj.save()
                serializer = BackendResponseSerializer(res_obj)
                return DRFResponse([serializer.data]) # Обернул в список, чтобы сохранить формат ответа
            else:
                return DRFResponse({"error": "AI вернул пустой результат или не нашел менеджера"}, status=500)
        except Exception as exc:
            return DRFResponse({"error": f"Ошибка при обработке тикета {ticket.client_guid}: {exc}"}, status=500)