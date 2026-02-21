from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Подключаем роуты из приложения api
    path('api/', include('api.urls')), 
]