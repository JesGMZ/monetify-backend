from django.urls import path
from . import views

urlpatterns = [
    path('estadisticas/', views.reporte_estadisticas, name='reporte-estadisticas'),
    path('grafico-ingresos-deudas/', views.grafico_ingresos_deudas, name='grafico-ingresos-deudas'),
    path('grafico-efectividad/', views.grafico_efectividad, name='grafico-efectividad'),
]