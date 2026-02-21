# api/management/commands/load_base_data.py
import csv
import os
from django.core.management.base import BaseCommand
from api.models import BusinessUnit, Manager

class Command(BaseCommand):
    help = 'Загружает Офисы и Менеджеров из CSV'

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        # 1. Загрузка Офисов
        bu_path = os.path.join(base_dir, 'business_units.csv')
        if os.path.exists(bu_path):
            with open(bu_path, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    BusinessUnit.objects.get_or_create(
                        name=row['Офис'],
                        defaults={'address': row['Адрес']}
                    )
            self.stdout.write(self.style.SUCCESS('Офисы загружены!'))

        # 2. Загрузка Менеджеров
        man_path = os.path.join(base_dir, 'managers.csv')
        if os.path.exists(man_path):
            with open(man_path, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    office = BusinessUnit.objects.filter(name=row['Офис']).first()
                    if office:
                        skills = [s.strip() for s in row['Навыки'].split(',')]
                        Manager.objects.get_or_create(
                            full_name=row['ФИО'],
                            defaults={
                                'position': row['Должность '].strip(),
                                'skills': skills,
                                'business_unit': office,
                                'current_load': int(row['Количество обращений в работе'] or 0)
                            }
                        )
            self.stdout.write(self.style.SUCCESS('Менеджеры загружены!'))