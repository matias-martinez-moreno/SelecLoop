# =============================================================================
# MODELOS DE LA BASE DE DATOS - SelecLoop
# =============================================================================
# Este archivo define la estructura completa de la base de datos para SelecLoop
# Cada modelo representa una tabla relacional con sus campos y relaciones
#
# Arquitectura: Modelo-Vista-Template (MVT) de Django
# Patrón: Object-Oriented Design con ORM (Object-Relational Mapping)
#
# Modelos principales:
# - Company: Empresas con información geo-localizada
# - Review: Reseñas de procesos de selección
# - UserProfile: Perfiles de usuario con roles específicos
# - StaffAssignment: Asignaciones de empresas a candidatos
# =============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


# =============================================================================
# MODELO: EMPRESA
# =============================================================================
# Modelo principal que representa una empresa en el sistema SelecLoop
# Almacena información completa de empresas incluyendo datos geo-localizados
# para funcionalidades de búsqueda por ubicación y optimización SEO local
#
# Relaciones:
# - One-to-Many con Review (una empresa puede tener muchas reseñas)
# - One-to-Many con StaffAssignment (asignaciones de staff)
# - One-to-One opcional con UserProfile (representante de empresa)
#
# Funcionalidades SEO/Geo:
# - Campos de ubicación estructurados (ciudad, región, país)
# - Información para meta tags dinámicos
# - Datos para structured data (JSON-LD)
# =============================================================================
class Company(models.Model):
    """
    Modelo que representa una empresa en el sistema SelecLoop.
    Almacena información completa incluyendo datos geo-localizados para
    funcionalidades de búsqueda por ubicación y optimización SEO.
    """
    
    # ===== CAMPOS BÁSICOS =====
    name = models.CharField(
        max_length=200,
        verbose_name="Nombre de la empresa",
        help_text="Nombre completo de la empresa - usado en SEO y títulos"
    )

    description = models.TextField(
        verbose_name="Descripción",
        help_text="Descripción detallada de la empresa y su actividad - usado en meta descriptions",
        blank=True
    )

    sector = models.CharField(
        max_length=100,
        verbose_name="Sector",
        help_text="Sector o industria de la empresa (ej: Tecnología, Salud, etc.) - usado para filtros"
    )

    # ===== CAMPOS GEO-LOCALIZACIÓN (SEO LOCAL) =====
    location = models.CharField(
        max_length=100,
        verbose_name="Ciudad",
        help_text="Ciudad principal de la empresa - usado para búsquedas geo y SEO local"
    )

    region = models.CharField(
        max_length=100,
        verbose_name="Región/Estado",
        help_text="Región, estado o departamento donde está ubicada la empresa - usado para filtros avanzados",
        blank=True,
        null=True
    )

    country = models.CharField(
        max_length=100,
        verbose_name="País",
        help_text="País donde está ubicada la empresa - usado en structured data y SEO internacional",
        default="Colombia"
    )
    
    website = models.URLField(
        verbose_name="Sitio web",
        help_text="URL del sitio web oficial de la empresa",
        blank=True,
        null=True
    )
    
    # ===== CAMPOS DE ESTADO =====
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa",
        help_text="Indica si la empresa está activa en el sistema"
    )
    
    # ===== CAMPOS DE FECHA =====
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )
    
    # ===== MÉTODOS =====
    def __str__(self):
        """Representación en string del modelo"""
        return self.name
    
    class Meta:
        """Configuración del modelo"""
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['name']  # Ordenar por nombre alfabéticamente

# ===== MODELO: PERFIL DE USUARIO =====
class UserProfile(models.Model):
    """
    Modelo que extiende el usuario de Django con información adicional.
    Define el rol del usuario y su relación con empresas.
    """
    
    # ===== CAMPOS DE RELACIÓN =====
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        verbose_name="Usuario",
        related_name="profile"
    )
    
    company = models.ForeignKey(
        Company, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        verbose_name="Empresa",
        help_text="Empresa a la que pertenece el usuario (si aplica)"
    )
    
    # ===== CAMPOS DE ROL =====
    ROLE_CHOICES = [
        ('candidate', 'Candidato'),           # Usuario que busca trabajo
        ('company_rep', 'Representante de Empresa'),  # Usuario de empresa
        ('staff', 'Staff del Sistema'),       # Administrador del sistema
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='candidate',
        verbose_name="Rol",
        help_text="Rol del usuario en el sistema"
    )
    
    # ===== CAMPOS ADICIONALES =====
    phone = models.CharField(
        max_length=20, 
        verbose_name="Teléfono",
        blank=True,
        null=True
    )
    
    bio = models.TextField(
        verbose_name="Biografía",
        help_text="Información personal del usuario",
        blank=True,
        null=True
    )

    # ===== CAMPOS DE PERFIL PÚBLICO =====
    display_name = models.CharField(
        max_length=100,
        verbose_name="Nombre visible",
        help_text="Nombre mostrado públicamente en tu perfil",
        blank=True
    )

    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name="Foto de perfil",
        help_text="Imagen opcional para tu perfil"
    )
    
    # ===== CAMPOS DE FECHA =====
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    # ===== MÉTODOS =====
    def __str__(self):
        """Representación en string del modelo"""
        return f"{self.user.username} - {self.get_role_display()}"
    
    class Meta:
        """Configuración del modelo"""
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"

# ===== MODELO: RESEÑA =====
class Review(models.Model):
    """
    Modelo que representa una reseña de un proceso de selección.
    Los candidatos pueden crear reseñas sobre empresas donde participaron.
    """
    
    # ===== CAMPOS DE RELACIÓN =====
    user_profile = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE,
        verbose_name="Perfil de usuario",
        related_name="reviews"
    )
    
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE,
        verbose_name="Empresa",
        related_name="reviews"
    )
    
    # ===== CAMPOS BÁSICOS =====
    job_title = models.CharField(
        max_length=200, 
        verbose_name="Cargo o puesto",
        help_text="Título del trabajo o puesto al que se postuló"
    )
    
    # ===== CAMPOS DE MODALIDAD =====
    MODALITY_CHOICES = [
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('híbrido', 'Híbrido'),
    ]
    
    modality = models.CharField(
        max_length=20,
        choices=MODALITY_CHOICES,
        verbose_name="Modalidad de trabajo",
        help_text="Tipo de trabajo ofrecido"
    )
    
    # ===== CAMPOS DE CALIFICACIÓN =====
    COMMUNICATION_CHOICES = [
        ('excellent', 'Excelente'),
        ('good', 'Buena'),
        ('regular', 'Regular'),
        ('poor', 'Mala'),
    ]
    
    communication_rating = models.CharField(
        max_length=20,
        choices=COMMUNICATION_CHOICES,
        verbose_name="Calificación de comunicación",
        help_text="Evaluación de la comunicación durante el proceso"
    )
    
    DIFFICULTY_CHOICES = [
        ('very_easy', 'Muy Fácil'),
        ('easy', 'Fácil'),
        ('moderate', 'Moderada'),
        ('difficult', 'Difícil'),
        ('very_difficult', 'Muy Difícil'),
    ]
    
    difficulty_rating = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        verbose_name="Calificación de dificultad",
        help_text="Nivel de dificultad del proceso de selección"
    )
    
    RESPONSE_TIME_CHOICES = [
        ('immediate', 'Inmediata'),
        ('same_day', 'Mismo día'),
        ('next_day', 'Al día siguiente'),
        ('few_days', 'En pocos días'),
        ('slow', 'Lenta'),
    ]
    
    response_time_rating = models.CharField(
        max_length=20,
        choices=RESPONSE_TIME_CHOICES,
        verbose_name="Calificación de tiempo de respuesta",
        help_text="Velocidad de respuesta de la empresa"
    )
    
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Calificación general",
        help_text="Calificación general del 1 al 5"
    )
    
    # ===== CAMPOS DE CONTENIDO =====
    pros = models.TextField(
        verbose_name="Aspectos positivos",
        help_text="Lo que te gustó del proceso de selección"
    )
    
    cons = models.TextField(
        verbose_name="Aspectos a mejorar",
        help_text="Lo que podría mejorar en el proceso"
    )
    
    interview_questions = models.TextField(
        verbose_name="Preguntas de entrevista",
        help_text="Preguntas que te hicieron durante la entrevista",
        blank=True,
        null=True
    )
    
    # ===== CAMPOS DE ESTADO =====
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Estado",
        help_text="Estado de aprobación de la reseña"
    )
    
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Aprobada",
        help_text="Indica si la reseña ha sido aprobada por el staff"
    )
    
    is_flagged = models.BooleanField(
        default=False,
        verbose_name="Marcada",
        help_text="Indica si la reseña ha sido marcada para revisión"
    )
    
    moderator_notes = models.TextField(
        verbose_name="Notas del moderador",
        help_text="Comentarios del staff sobre la reseña",
        blank=True,
        null=True
    )

    # ===== CONTENIDO MULTIMEDIA OPCIONAL =====
    image = models.ImageField(
        upload_to='review_images/',
        null=True,
        blank=True,
        verbose_name="Imagen adjunta",
        help_text="Adjunta una imagen relacionada con tu experiencia (opcional)"
    )
    
    # ===== CAMPOS DE FECHA =====
    submission_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de envío"
    )
    
    approval_date = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Fecha de aprobación"
    )
    
    # ===== MÉTODOS =====
    def __str__(self):
        """Representación en string del modelo"""
        return f"Reseña de {self.user_profile.user.username} para {self.company.name}"
    
    class Meta:
        """Configuración del modelo"""
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"
        ordering = ['-submission_date']  # Ordenar por fecha de envío (más reciente primero)

# ===== MODELO: ESTADO DE ONBOARDING =====
class OnboardingStatus(models.Model):
    """
    Modelo que rastrea el estado de onboarding de un usuario.
    Ayuda a determinar si el usuario ha completado el proceso inicial.
    """
    
    # ===== CAMPOS DE RELACIÓN =====
    user_profile = models.OneToOneField(
        UserProfile, 
        on_delete=models.CASCADE,
        verbose_name="Perfil de usuario",
        related_name="onboarding_status"
    )
    
    # ===== CAMPOS DE ESTADO =====
    has_participated_in_selection = models.BooleanField(
        default=False,
        verbose_name="Ha participado en selección",
        help_text="Indica si el usuario ha participado en algún proceso de selección"
    )
    
    onboarding_completed = models.BooleanField(
        default=False,
        verbose_name="Onboarding completado",
        help_text="Indica si el usuario ha completado el proceso de onboarding"
    )
    
    # ===== CAMPOS DE FECHA =====
    last_onboarding_date = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Última fecha de onboarding"
    )
    
    # ===== MÉTODOS =====
    def detect_participation_status(self):
        """Detecta automáticamente si el usuario ha participado en algún proceso"""
        # Verifica si tiene reseñas pendientes o completadas
        has_pending = hasattr(self.user_profile, 'pending_reviews') and self.user_profile.pending_reviews.filter(is_reviewed=False).exists()
        has_reviews = hasattr(self.user_profile, 'reviews') and self.user_profile.reviews.exists()
        
        self.has_participated_in_selection = has_pending or has_reviews
        self.save()
    
    def __str__(self):
        """Representación en string del modelo"""
        return f"Onboarding de {self.user_profile.user.username}"
    
    class Meta:
        """Configuración del modelo"""
        verbose_name = "Estado de Onboarding"
        verbose_name_plural = "Estados de Onboarding"

# ===== MODELO: RESEÑA PENDIENTE =====
class PendingReview(models.Model):
    """
    Modelo que representa una reseña pendiente que debe ser completada.
    Se crea cuando el staff asigna una empresa a un usuario.
    """
    
    # ===== CAMPOS DE RELACIÓN =====
    user_profile = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE,
        verbose_name="Perfil de usuario",
        related_name="pending_reviews"
    )
    
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE,
        verbose_name="Empresa",
        related_name="pending_reviews"
    )
    
    # ===== CAMPOS BÁSICOS =====
    job_title = models.CharField(
        max_length=200, 
        verbose_name="Cargo o puesto",
        help_text="Título del trabajo o puesto al que se postuló"
    )
    
    participation_date = models.DateField(
        verbose_name="Fecha de participación",
        help_text="Fecha en que el usuario participó en el proceso de selección"
    )
    
    # ===== CAMPOS DE ESTADO =====
    is_reviewed = models.BooleanField(
        default=False,
        verbose_name="Reseña completada",
        help_text="Indica si el usuario ya completó la reseña"
    )
    
    # ===== CAMPOS DE FECHA =====
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    # ===== MÉTODOS =====
    def __str__(self):
        """Representación en string del modelo"""
        return f"Reseña pendiente de {self.user_profile.user.username} para {self.company.name}"
    
    class Meta:
        """Configuración del modelo"""
        verbose_name = "Reseña Pendiente"
        verbose_name_plural = "Reseñas Pendientes"
        ordering = ['-participation_date']  # Ordenar por fecha de participación

# ===== MODELO: ASIGNACIÓN DE STAFF =====
class StaffAssignment(models.Model):
    """
    Modelo que registra las asignaciones de empresas a usuarios realizadas por el staff.
    Permite rastrear quién asignó qué empresa a qué usuario.
    """
    
    # ===== CAMPOS DE RELACIÓN =====
    user_profile = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE,
        verbose_name="Perfil de usuario",
        related_name="staff_assignments"
    )
    
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE,
        verbose_name="Empresa",
        related_name="staff_assignments"
    )
    
    staff_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name="Usuario del staff",
        related_name="assignments_made"
    )
    
    # ===== CAMPOS BÁSICOS =====
    job_title = models.CharField(
        max_length=200, 
        verbose_name="Cargo o puesto",
        help_text="Título del trabajo o puesto al que se postuló el usuario"
    )
    
    participation_date = models.DateField(
        verbose_name="Fecha de participación",
        help_text="Fecha en que el usuario participó en el proceso de selección"
    )
    
    # ===== CAMPOS DE ESTADO =====
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa",
        help_text="Indica si la asignación está activa"
    )
    
    # ===== CAMPOS DE FECHA =====
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    # ===== MÉTODOS =====
    def create_pending_review(self):
        """Crea automáticamente una reseña pendiente cuando se asigna una empresa"""
        PendingReview.objects.create(
            user_profile=self.user_profile,
            company=self.company,
            job_title=self.job_title,
            participation_date=self.participation_date
        )
    
    def __str__(self):
        """Representación en string del modelo"""
        return f"Asignación: {self.user_profile.user.username} -> {self.company.name}"
    
    class Meta:
        """Configuración del modelo"""
        verbose_name = "Asignación de Staff"
        verbose_name_plural = "Asignaciones de Staff"
        ordering = ['-created_at']  # Ordenar por fecha de creación