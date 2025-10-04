# ===== CONFIGURACIÓN DEL PANEL DE ADMINISTRACIÓN =====
# Configuración del admin para los modelos de accounts

from django.contrib import admin
from .models import UserProfile, OnboardingStatus

# ===== ADMIN: PERFILES DE USUARIO =====
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo UserProfile.
    Permite gestionar perfiles de usuario desde el panel de administración.
    """
    
    # ===== CAMPOS MOSTRADOS EN LA LISTA =====
    list_display = [
        'user',           # Usuario asociado
        'role',           # Rol del usuario
        'company',        # Empresa asociada
        'phone',          # Teléfono del usuario
        'created_at'      # Fecha de creación
    ]
    
    # ===== FILTROS DISPONIBLES =====
    list_filter = [
        'role',           # Filtrar por rol
        'company',        # Filtrar por empresa
        'created_at'      # Filtrar por fecha de creación
    ]
    
    # ===== CAMPOS DE BÚSQUEDA =====
    search_fields = [
        'user__username', # Buscar por nombre de usuario
        'user__email',    # Buscar por email
        'phone'           # Buscar por teléfono
    ]
    
    # ===== ORDENAMIENTO =====
    ordering = ['user__username']  # Ordenar alfabéticamente por nombre de usuario

# ===== ADMIN: ESTADOS DE ONBOARDING =====
@admin.register(OnboardingStatus)
class OnboardingStatusAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo OnboardingStatus.
    Permite gestionar el estado de onboarding de los usuarios desde el panel de administración.
    """
    
    # ===== CAMPOS MOSTRADOS EN LA LISTA =====
    list_display = [
        'user_profile',                   # Usuario
        'has_participated_in_selection',  # Si ha participado en selección
        'onboarding_completed',           # Si completó el onboarding
        'last_onboarding_date'            # Última fecha de onboarding
    ]
    
    # ===== FILTROS DISPONIBLES =====
    list_filter = [
        'has_participated_in_selection',  # Filtrar por participación
        'onboarding_completed',           # Filtrar por completado
        'last_onboarding_date'            # Filtrar por fecha
    ]
    
    # ===== CAMPOS DE BÚSQUEDA =====
    search_fields = [
        'user_profile__user__username'   # Buscar por nombre de usuario
    ]
    
    # ===== ORDENAMIENTO =====
    ordering = ['user_profile__user__username']  # Ordenar alfabéticamente por nombre de usuario