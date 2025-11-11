# ===== URLs DE LA APLICACIÓN COMPANIES =====
# Este archivo define las rutas relacionadas con empresas

from django.urls import path
from . import views

# ===== PATRONES DE URL =====
urlpatterns = [
    # ===== GESTIÓN DE EMPRESAS =====
    # Vista detallada de una empresa específica
    path('company/<int:company_id>/', views.company_detail_view, name='company_detail'),
    
    # Dashboard para representantes de empresa
    path('company-dashboard/', views.company_dashboard_view, name='company_dashboard'),
    
    # Editar empresa (solo para company_rep)
    path('company/<int:company_id>/edit/', views.edit_company_view, name='edit_company'),
    
    # Exportar reportes
    path('company/<int:company_id>/export/excel/', views.export_company_report_excel, name='export_company_report_excel'),
]
