# ===== CONFIGURACIÓN DEL PANEL DE ADMINISTRACIÓN =====
# Este archivo configura cómo se muestran los modelos en el admin de Django
# Permite al staff gestionar usuarios, empresas, reseñas y asignaciones

from django.contrib import admin
from .models import Company, UserProfile, Review, OnboardingStatus, PendingReview, StaffAssignment

# ===== ADMIN: EMPRESAS =====
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Company.
    Permite gestionar empresas desde el panel de administración.
    """
    
    # ===== CAMPOS MOSTRADOS EN LA LISTA =====
    list_display = [
        'name',           # Nombre de la empresa
        'sector',         # Sector de la empresa
        'location',       # Ubicación de la empresa
        'is_active',      # Estado activo/inactivo
        'created_at'      # Fecha de creación
    ]
    
    # ===== FILTROS DISPONIBLES =====
    list_filter = [
        'sector',         # Filtrar por sector
        'location',       # Filtrar por ubicación
        'is_active',      # Filtrar por estado
        'created_at'      # Filtrar por fecha de creación
    ]
    
    # ===== CAMPOS DE BÚSQUEDA =====
    search_fields = [
        'name',           # Buscar por nombre
        'sector',         # Buscar por sector
        'location'        # Buscar por ubicación
    ]
    
    # ===== CAMPOS EDITABLES EN LA LISTA =====
    list_editable = ['is_active']  # Cambiar estado sin entrar al detalle
    
    # ===== ORDENAMIENTO =====
    ordering = ['name']  # Ordenar alfabéticamente por nombre

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

# ===== ADMIN: ASIGNACIONES DE STAFF =====
@admin.register(StaffAssignment)
class StaffAssignmentAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo StaffAssignment.
    Permite gestionar las asignaciones de empresas a usuarios realizadas por el staff.
    """
    
    # ===== CAMPOS MOSTRADOS EN LA LISTA =====
    list_display = [
        'user_profile',       # Usuario asignado
        'company',            # Empresa asignada
        'job_title',          # Cargo o puesto
        'participation_date', # Fecha de participación
        'staff_user',         # Staff que realizó la asignación
        'is_active',          # Estado de la asignación
        'created_at'          # Fecha de creación
    ]
    
    # ===== FILTROS DISPONIBLES =====
    list_filter = [
        'is_active',          # Filtrar por estado activo
        'participation_date', # Filtrar por fecha de participación
        'created_at',         # Filtrar por fecha de creación
        'staff_user'          # Filtrar por staff que asignó
    ]
    
    # ===== CAMPOS DE BÚSQUEDA =====
    search_fields = [
        'user_profile__user__username',  # Buscar por nombre de usuario
        'company__name',                 # Buscar por nombre de empresa
        'job_title',                     # Buscar por cargo
        'staff_user__username'           # Buscar por staff
    ]
    
    # ===== CAMPOS EDITABLES EN LA LISTA =====
    list_editable = ['is_active']  # Cambiar estado sin entrar al detalle
    
    # ===== ORDENAMIENTO =====
    ordering = ['-created_at']  # Ordenar por fecha de creación (más reciente primero)
    
    # ===== MÉTODOS PERSONALIZADOS =====
    def save_model(self, request, obj, form, change):
        """
        Método personalizado que se ejecuta al guardar una asignación.
        Crea automáticamente un PendingReview cuando se guarda.
        """
        super().save_model(request, obj, form, change)
        if obj.is_active:
            obj.create_pending_review()

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