import os, sys, django
sys.path.insert(0, os.path.abspath('datazavr'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from datazavr.api.models import Ticket, Manager, BusinessUnit
from classificator.classificate import classificate
ticket = Ticket.objects.get(client_guid='ba61a4e7-f0f1-f011-8406-0022481ba51f')
all_units = list(BusinessUnit.objects.all())
all_managers = list(Manager.objects.all())
classificate(ticket, all_units, all_managers)
