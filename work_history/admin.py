# ===== CONFIGURACIÓN DEL PANEL DE ADMINISTRACIÓN =====
# Configuración del admin para los modelos de work_history

from django.contrib import admin
from .models import WorkHistory

# ===== ADMIN: HISTORIAL LABORAL =====
@admin.register(WorkHistory)
class WorkHistoryAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo WorkHistory.
    Permite gestionar el historial laboral de los usuarios desde el panel de administración.
    """
    
    # ===== CAMPOS MOSTRADOS EN LA LISTA =====
    list_display = [
        'user_profile',       # Usuario
        'company',            # Empresa
        'job_title',          # Cargo o puesto
        'start_date',         # Fecha de inicio
        'end_date',           # Fecha de finalización
        'is_current_job',     # Si es trabajo actual
        'has_review_pending', # Si tiene reseña pendiente
        'created_at'          # Fecha de creación
    ]
    
    # ===== FILTROS DISPONIBLES =====
    list_filter = [
        'is_current_job',     # Filtrar por trabajo actual
        'has_review_pending', # Filtrar por reseña pendiente
        'start_date',         # Filtrar por fecha de inicio
        'created_at'          # Filtrar por fecha de creación
    ]
    
    # ===== CAMPOS DE BÚSQUEDA =====
    search_fields = [
        'user_profile__user__username',  # Buscar por nombre de usuario
        'company__name',                 # Buscar por nombre de empresa
        'job_title'                      # Buscar por cargo
    ]
    
    # ===== CAMPOS EDITABLES EN LA LISTA =====
    list_editable = ['is_current_job', 'has_review_pending']  # Cambiar estado sin entrar al detalle
    
    # ===== ORDENAMIENTO =====
    ordering = ['-start_date']  # Ordenar por fecha de inicio (más reciente primero)