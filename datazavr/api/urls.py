from django.urls import path
from .views import ProcessedTicketsAPIView

urlpatterns = [
    path('tickets/', ProcessedTicketsAPIView.as_view(), name='tickets'),
]