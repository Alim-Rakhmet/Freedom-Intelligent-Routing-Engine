import csv
import os
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response as DRFResponse
from .models import Ticket, Response
from .serializers import BackendResponseSerializer
from .services import analyze_text_with_llm, find_best_manager

class ProcessedTicketsAPIView(APIView):
    def get(self, request):
        responses = Response.objects.select_related('ticket', 'assigned_manager', 'assigned_manager__business_unit').order_by('-created_at')
        serializer = BackendResponseSerializer(responses, many=True)
        return DRFResponse(serializer.data)

    def post(self, request):
        # Ищем tickets.csv в корне проекта (там же, где manage.py)
        file_path = os.path.join(settings.BASE_DIR, 'tickets.csv')
        
        if not os.path.exists(file_path):
            return DRFResponse({"error": "Файл tickets.csv не найден на сервере!"}, status=404)

        # Очищаем старые данные перед новым запуском (чтобы не было дублей на демо)
        Response.objects.all().delete()
        Ticket.objects.all().delete()

        processed_responses = []

        with open(file_path, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                description = row.get('Описание ', '')
                birth_date_raw = row.get('Дата рождения', '')
                clean_date = birth_date_raw.split(' ')[0] if birth_date_raw else "2000-01-01"

                # 1. Создаем Ticket
                ticket = Ticket.objects.create(
                    client_guid=row.get('GUID клиента'),
                    gender=row.get('Пол клиента'),
                    birth_date=clean_date,
                    segment=row.get('Сегмент клиента'),
                    description=description,
                    country=row.get('Страна'),
                    region=row.get('Область'),
                    city=row.get('Населённый пункт'),
                    street=row.get('Улица'),
                    house=row.get('Дом')
                )

                # 2. ИИ-анализ
                ai_data = analyze_text_with_llm(description)

                # 3. Маршрутизация
                best_manager = find_best_manager(
                    city=ticket.city,
                    segment=ticket.segment,
                    issue_type=ai_data['type'],
                    language=ai_data['language']
                )

                # 4. Создаем Response
                response_obj = Response.objects.create(
                    ticket=ticket,
                    issue_type=ai_data['type'],
                    sentiment=ai_data['sentiment'],
                    priority=ai_data['priority'],
                    language=ai_data['language'],
                    summary=ai_data['summary'],
                    assigned_manager=best_manager
                )
                processed_responses.append(response_obj)

        serializer = BackendResponseSerializer(processed_responses, many=True)
        return DRFResponse(serializer.data)