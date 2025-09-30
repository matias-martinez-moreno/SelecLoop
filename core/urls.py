# ===== URLs DE LA APLICACIÓN CORE =====
# Este archivo define todas las rutas de la aplicación principal
# Cada URL está conectada a una vista específica en views.py

from django.urls import path
from . import views

# ===== PATRONES DE URL =====
urlpatterns = [
    # ===== PÁGINAS PRINCIPALES =====
    # Página de inicio - redirige según el rol del usuario
    path('', views.root_redirect_view, name='root'),
    
    # ===== AUTENTICACIÓN =====
    # Página de login
    path('login/', views.login_view, name='login'),
    
    # Cerrar sesión
    path('logout/', views.logout_view, name='logout'),
    
    # ===== DASHBOARDS POR ROL =====
    # Dashboard principal para candidatos
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Dashboard para representantes de empresa
    path('company-dashboard/', views.company_dashboard_view, name='company_dashboard'),
    
    # Dashboard para el staff del sistema (eliminado)
    
    # ===== GESTIÓN DE EMPRESAS =====
    # Vista detallada de una empresa específica
    path('company/<int:company_id>/', views.company_detail_view, name='company_detail'),
    
    # ===== GESTIÓN DE RESEÑAS =====
    # Crear una nueva reseña
    path('create-review/', views.create_review_view, name='create_review'),
    
    # Ver las reseñas del usuario actual
    path('my-reviews/', views.my_reviews_view, name='my_reviews'),
    
    # ===== GESTIÓN DE PERFIL =====
    # Ver y editar el perfil del usuario
    path('profile/', views.my_profile_view, name='my_profile'),
    path('profile/update/', views.update_profile_view, name='update_profile'),
    
    # ===== GESTIÓN DE HISTORIAL LABORAL =====
    # Ver historial laboral del usuario
    path('work-history/', views.work_history_view, name='work_history'),
    
    # Agregar nueva experiencia laboral
    path('add-work-history/', views.add_work_history_view, name='add_work_history'),
    
    # ===== SISTEMA DE LOGROS =====
    # Ver logros del usuario
    path('achievements/', views.achievements_view, name='achievements'),
    
    # ===== VISTAS DEL STAFF =====
    # (Eliminadas - ahora se usa moderación automática con machine learning)
    # Export CSV de reseñas por empresa (solo company_rep/staff)
    path('company/<int:company_id>/export-reviews.csv', views.export_company_reviews_csv, name='export_company_reviews_csv'),

    # ===== VISTAS SEO =====
    # Robots.txt para motores de búsqueda
    path('robots.txt', views.robots_txt_view, name='robots_txt'),

    # Sitemap.xml para motores de búsqueda
    path('sitemap.xml', views.sitemap_xml_view, name='sitemap'),
]