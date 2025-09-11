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
    
    # Dashboard para el staff del sistema
    path('staff-dashboard/', views.staff_dashboard_view, name='staff_dashboard'),
    
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
    
    # ===== VISTAS DEL STAFF =====
    # Crear nuevos usuarios (solo staff)
    path('staff/create-user/', views.create_user_view, name='staff_create_user'),
    
    # Asignar empresas a usuarios (solo staff)
    path('staff/assign-company/', views.assign_company_view, name='staff_assign_company'),
    
    # Eliminar reseñas (solo staff)
    path('staff/delete-review/<int:review_id>/', views.delete_review_view, name='staff_delete_review'),
    
    # Aprobar o rechazar reseñas (solo staff)
    path('staff/manage-review/<int:review_id>/', views.approve_review_view, name='staff_manage_review'),
]