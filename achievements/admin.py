# ===== CONFIGURACIÓN DEL PANEL DE ADMINISTRACIÓN =====
# Configuración del admin para los modelos de achievements

from django.contrib import admin
from .models import Achievement, UserAchievement

# ===== ADMIN: LOGROS =====
@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Achievement.
    Permite gestionar logros desde el panel de administración.
    """
    
    # ===== CAMPOS MOSTRADOS EN LA LISTA =====
    list_display = [
        'name',           # Nombre del logro
        'achievement_type', # Tipo de logro
        'required_value', # Valor requerido
        'color',          # Color del logro
        'is_active',      # Estado activo
        'created_at'      # Fecha de creación
    ]
    
    # ===== FILTROS DISPONIBLES =====
    list_filter = [
        'achievement_type', # Filtrar por tipo
        'color',           # Filtrar por color
        'is_active',       # Filtrar por estado
        'created_at'       # Filtrar por fecha
    ]
    
    # ===== CAMPOS DE BÚSQUEDA =====
    search_fields = [
        'name',           # Buscar por nombre
        'description'     # Buscar por descripción
    ]
    
    # ===== CAMPOS EDITABLES EN LA LISTA =====
    list_editable = ['is_active']  # Cambiar estado sin entrar al detalle
    
    # ===== ORDENAMIENTO =====
    ordering = ['achievement_type', 'required_value']

# ===== ADMIN: LOGROS DE USUARIO =====
@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo UserAchievement.
    Permite gestionar logros de usuarios desde el panel de administración.
    """
    
    # ===== CAMPOS MOSTRADOS EN LA LISTA =====
    list_display = [
        'user_profile',   # Usuario
        'achievement',    # Logro
        'earned_at'       # Fecha de obtención
    ]
    
    # ===== FILTROS DISPONIBLES =====
    list_filter = [
        'achievement__achievement_type', # Filtrar por tipo de logro
        'achievement__color',           # Filtrar por color
        'earned_at'                     # Filtrar por fecha
    ]
    
    # ===== CAMPOS DE BÚSQUEDA =====
    search_fields = [
        'user_profile__user__username', # Buscar por nombre de usuario
        'achievement__name'             # Buscar por nombre del logro
    ]
    
    # ===== ORDENAMIENTO =====
    ordering = ['-earned_at']  # Ordenar por fecha de obtención (más reciente primero)