from rest_framework import serializers
from .models import Ticket, Manager, BusinessUnit, Response

class BusinessUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessUnit
        fields = ['name', 'address']

class ManagerSerializer(serializers.ModelSerializer):
    business_unit = BusinessUnitSerializer()

    class Meta:
        model = Manager
        fields = ['full_name', 'position', 'skills', 'business_unit', 'current_load']

class BackendResponseSerializer(serializers.ModelSerializer):
    ticket = serializers.SerializerMethodField()
    
    # ВОТ ЗДЕСЬ ГЛАВНОЕ ИЗМЕНЕНИЕ: мы используем SerializerMethodField вместо source=...
    manager = serializers.SerializerMethodField()
    business_unit = serializers.SerializerMethodField()
    
    type = serializers.CharField(source='issue_type')
    
    class Meta:
        model = Response
        fields = ['ticket', 'manager', 'business_unit', 'type', 'sentiment', 'priority', 'language', 'summary']

    def get_ticket(self, obj):
        t = obj.ticket 
        return {
            "client_guid": str(t.client_guid),
            "gender": t.gender,
            "birth_date": str(t.birth_date) if t.birth_date else "",
            "segment": t.segment,
            "description": t.description,
            "country": t.country,
            "region": t.region,
            "city": t.city,
            "street": t.street,
            "house": t.house,
            "attachments": []
        }

    # Безопасно достаем менеджера
    def get_manager(self, obj):
        if obj.assigned_manager:
            return ManagerSerializer(obj.assigned_manager).data
        return None # Если менеджера нет, просто вернем null, без ошибок

    # Безопасно достаем офис
    def get_business_unit(self, obj):
        if obj.assigned_manager and obj.assigned_manager.business_unit:
            return BusinessUnitSerializer(obj.assigned_manager.business_unit).data
        return None # Если офиса нет, вернем null