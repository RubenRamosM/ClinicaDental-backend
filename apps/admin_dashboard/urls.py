"""
URLs para dashboard administrativo.
"""
from django.urls import path
from . import views

urlpatterns = [
    # CU26: Dashboard Administrativo
    path('', views.dashboard_general, name='dashboard-general'),
    path('financiero/', views.dashboard_financiero, name='dashboard-financiero'),
    path('operaciones/', views.dashboard_operaciones, name='dashboard-operaciones'),
    
    # CU25: Reportes
    path('citas/', views.reporte_citas, name='reporte-citas'),
    path('tratamientos/', views.reporte_tratamientos, name='reporte-tratamientos'),
    path('ingresos/', views.reporte_ingresos, name='reporte-ingresos'),
    path('pacientes/', views.reporte_pacientes, name='reporte-pacientes'),
]
