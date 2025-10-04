# ===== CONFIGURACIÓN DEL PANEL DE ADMINISTRACIÓN =====
# Configuración del admin para los modelos de reviews

from django.contrib import admin
from .models import Review, PendingReview

# ===== ADMIN: RESEÑAS =====
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Review.
    Permite gestionar reseñas de procesos de selección desde el panel de administración.
    """
    
    # ===== CAMPOS MOSTRADOS EN LA LISTA =====
    list_display = [
        'user_profile',       # Usuario que creó la reseña
        'company',            # Empresa evaluada
        'job_title',          # Cargo o puesto
        'overall_rating',     # Calificación general
        'status',             # Estado de la reseña
        'is_approved',        # Si está aprobada
        'submission_date'     # Fecha de envío
    ]
    
    # ===== FILTROS DISPONIBLES =====
    list_filter = [
        'status',             # Filtrar por estado
        'is_approved',        # Filtrar por aprobación
        'overall_rating',     # Filtrar por calificación
        'modality',           # Filtrar por modalidad
        'submission_date'     # Filtrar por fecha de envío
    ]
    
    # ===== CAMPOS DE BÚSQUEDA =====
    search_fields = [
        'user_profile__user__username',  # Buscar por nombre de usuario
        'company__name',                 # Buscar por nombre de empresa
        'job_title'                      # Buscar por cargo
    ]
    
    # ===== CAMPOS EDITABLES EN LA LISTA =====
    list_editable = ['status']  # Cambiar estado sin entrar al detalle
    
    # ===== ORDENAMIENTO =====
    ordering = ['-submission_date']  # Ordenar por fecha de envío (más reciente primero)
    
    # ===== AGRUPACIÓN DE CAMPOS =====
    fieldsets = (
        # Grupo: Información Básica
        ('Información Básica', {
            'fields': ('user_profile', 'company', 'job_title', 'modality')
        }),
        # Grupo: Calificaciones
        ('Calificaciones', {
            'fields': ('communication_rating', 'difficulty_rating', 'response_time_rating', 'overall_rating')
        }),
        # Grupo: Contenido
        ('Contenido', {
            'fields': ('pros', 'cons', 'interview_questions')
        }),
        # Grupo: Estado
        ('Estado', {
            'fields': ('status', 'is_approved', 'is_flagged', 'moderator_notes')
        }),
        # Grupo: Fechas
        ('Fechas', {
            'fields': ('submission_date', 'approval_date')
        })
    )

# ===== ADMIN: RESEÑAS PENDIENTES =====
@admin.register(PendingReview)
class PendingReviewAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo PendingReview.
    Permite gestionar reseñas pendientes desde el panel de administración.
    """
    
    # ===== CAMPOS MOSTRADOS EN LA LISTA =====
    list_display = [
        'user_profile',       # Usuario con reseña pendiente
        'company',            # Empresa para la que debe crear reseña
        'job_title',          # Cargo o puesto
        'participation_date', # Fecha de participación
        'is_reviewed',        # Si ya completó la reseña
        'created_at'          # Fecha de creación
    ]
    
    # ===== FILTROS DISPONIBLES =====
    list_filter = [
        'is_reviewed',        # Filtrar por estado de reseña
        'participation_date', # Filtrar por fecha de participación
        'created_at'          # Filtrar por fecha de creación
    ]
    
    # ===== CAMPOS DE BÚSQUEDA =====
    search_fields = [
        'user_profile__user__username',  # Buscar por nombre de usuario
        'company__name',                 # Buscar por nombre de empresa
        'job_title'                      # Buscar por cargo
    ]
    
    # ===== CAMPOS EDITABLES EN LA LISTA =====
    list_editable = ['is_reviewed']  # Cambiar estado sin entrar al detalle
    
    # ===== ORDENAMIENTO =====
    ordering = ['-participation_date']  # Ordenar por fecha de participación