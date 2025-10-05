# =============================================================================
# MODELOS DE LA APLICACIÓN REVIEWS - SelecLoop
# =============================================================================
# Este archivo define los modelos relacionados con reseñas
#
# Modelos:
# - Review: Reseñas de procesos de selección
# - PendingReview: Reseñas pendientes asignadas por staff
# =============================================================================

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# ===== MODELO: RESEÑA =====
class Review(models.Model):
    """
    Modelo que representa una reseña de un proceso de selección.
    Los candidatos pueden crear reseñas sobre empresas donde participaron.
    """
    
    # ===== CAMPOS DE RELACIÓN =====
    user_profile = models.ForeignKey(
        'accounts.UserProfile', 
        on_delete=models.CASCADE,
        verbose_name="Perfil de usuario",
        related_name="reviews"
    )
    
    company = models.ForeignKey(
        'companies.Company', 
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


# ===== MODELO: RESEÑA PENDIENTE =====
class PendingReview(models.Model):
    """
    Modelo que representa una reseña pendiente que debe ser completada.
    Se crea cuando el staff asigna una empresa a un usuario.
    """
    
    # ===== CAMPOS DE RELACIÓN =====
    user_profile = models.ForeignKey(
        'accounts.UserProfile', 
        on_delete=models.CASCADE,
        verbose_name="Perfil de usuario",
        related_name="pending_reviews"
    )
    
    company = models.ForeignKey(
        'companies.Company', 
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
        unique_together = ['user_profile', 'company', 'job_title']  # Evitar duplicados