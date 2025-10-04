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
    
    # ===== GESTIÓN DE PERFIL =====
    # Ver y editar el perfil del usuario
    path('profile/', views.my_profile_view, name='my_profile'),
    path('profile/update/', views.update_profile_view, name='update_profile'),
]
