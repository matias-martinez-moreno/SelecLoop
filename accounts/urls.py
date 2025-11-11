# ===== URLs DE LA APLICACIÓN ACCOUNTS =====
# Este archivo define las rutas relacionadas con usuarios y autenticación

from django.urls import path
from . import views

# ===== PATRONES DE URL =====
urlpatterns = [
    # ===== AUTENTICACIÓN =====
    # Página de login
    path('login/', views.login_view, name='login'),
    
    # Cerrar sesión
    path('logout/', views.logout_view, name='logout'),
    
    # Recuperación de contraseña
    path('password-reset/', views.password_reset_request_view, name='password_reset'),
    path('password-reset/confirm/', views.password_reset_confirm_view, name='password_reset_confirm'),
    
    # ===== GESTIÓN DE PERFIL =====
    # Ver y editar el perfil del usuario
    path('profile/', views.my_profile_view, name='my_profile'),
    path('profile/update/', views.update_profile_view, name='update_profile'),
    path('profile/<int:user_id>/', views.view_user_profile_view, name='view_user_profile'),
]
