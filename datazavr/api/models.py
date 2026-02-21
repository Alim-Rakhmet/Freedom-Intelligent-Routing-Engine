from django.db import models
import uuid

class BusinessUnit(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()

class Manager(models.Model):
    full_name = models.CharField(max_length=255)
    position = models.CharField(max_length=100)
    skills = models.JSONField()
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    current_load = models.IntegerField(default=0)

class Ticket(models.Model):
    client_guid = models.UUIDField(default=uuid.uuid4)
    gender = models.CharField(max_length=50)
    birth_date = models.DateField()
    segment = models.CharField(max_length=50)
    description = models.TextField()
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=255)
    house = models.CharField(max_length=50)

class Response(models.Model):
    # СВЯЗЬ С ТИКЕТОМ (обязательно нужна, чтобы знать чей это результат)
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='ai_response')

    # ИИ Анализ
    issue_type = models.CharField(max_length=100)
    sentiment = models.CharField(max_length=50)
    priority = models.IntegerField()
    language = models.CharField(max_length=10)
    summary = models.TextField()

    # Результат
    assigned_manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)