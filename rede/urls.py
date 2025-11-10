from django.urls import path
from . import views

app_name = 'rede'

urlpatterns = [
    path('portas-por-equipamento/', views.portas_por_equipamento, name='portas_por_equipamento'),
]
