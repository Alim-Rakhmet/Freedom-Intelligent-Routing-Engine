# api/management/commands/load_base_data.py
import csv
import os
from django.core.management.base import BaseCommand
from api.models import BusinessUnit, Manager

class Command(BaseCommand):
    help = 'Загружает Офисы и Менеджеров из CSV'

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        data_dir = os.path.join(base_dir, 'data')
        
        # 1. Загрузка Офисов
        bu_path = os.path.join(data_dir, 'business_units.csv')
        if os.path.exists(bu_path):
            with open(bu_path, encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    office_name = row.get('Офис', '').strip()
                    office_address = row.get('Адрес', '').strip()
                    
                    # Проверяем, есть ли уже такой офис, чтобы не упасть с MultipleObjectsReturned
                    office = BusinessUnit.objects.filter(name=office_name).first()
                    if not office:
                        BusinessUnit.objects.create(name=office_name, address=office_address)
            self.stdout.write(self.style.SUCCESS('Офисы загружены!'))

        # 2. Загрузка Менеджеров
        man_path = os.path.join(data_dir, 'managers.csv')
        if os.path.exists(man_path):
            with open(man_path, encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    office_name = row.get('Офис', '').strip()
                    office = BusinessUnit.objects.filter(name__icontains=office_name).first()
                    if office:
                        skills_raw = row.get('Навыки', '')
                        skills = [s.strip() for s in skills_raw.split(',')] if skills_raw else []
                        manager_name = row.get('ФИО', '').strip()
                        
                        manager = Manager.objects.filter(full_name=manager_name).first()
                        if not manager:
                            Manager.objects.create(
                                full_name=manager_name,
                                position=row.get('Должность ', row.get('Должность', '')).strip(),
                                skills=skills,
                                business_unit=office,
                                current_load=int(row.get('Количество обращений в работе', '0') or 0)
                            )
            self.stdout.write(self.style.SUCCESS('Менеджеры загружены!'))