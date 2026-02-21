import os
from django.core.wsgi import get_wsgi_application

# ЗАМЕНИ 'core' на название твоей папки проекта
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()