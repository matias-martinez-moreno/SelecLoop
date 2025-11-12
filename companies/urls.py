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
    
    # Reseñas de la empresa (para company_rep)
    path('company-reviews/', views.company_reviews_view, name='company_reviews'),
    
    # Dashboard para staff
    path('staff-dashboard/', views.staff_dashboard_view, name='staff_dashboard'),
    
    # Editar empresa (para company_rep y staff)
    path('company/<int:company_id>/edit/', views.edit_company_view, name='edit_company'),
    
    # Crear empresa (solo staff)
    path('company/create/', views.create_company_view, name='create_company'),
    
    # Activar/desactivar empresa (solo staff)
    path('company/<int:company_id>/toggle-status/', views.toggle_company_status_view, name='toggle_company_status'),
    
    # Borrar empresa (solo staff)
    path('company/<int:company_id>/delete/', views.delete_company_view, name='delete_company'),
    
    # Borrar reseña (solo staff)
    path('review/<int:review_id>/delete/', views.delete_review_view, name='delete_review'),
    
    # Exportar reportes
    path('company/<int:company_id>/export/excel/', views.export_company_report_excel, name='export_company_report_excel'),
]
