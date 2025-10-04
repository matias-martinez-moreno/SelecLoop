# =============================================================================
# MODELOS DE LA APLICACIÓN WORK_HISTORY - SelecLoop
# =============================================================================
# Este archivo define los modelos relacionados con historial laboral
#
# Modelos:
# - WorkHistory: Historial laboral de usuarios
# =============================================================================

from django.db import models


# ===== MODELO: HISTORIAL LABORAL =====
class WorkHistory(models.Model):
    """
    Modelo que representa el historial laboral de un usuario.
    Permite a los candidatos agregar empresas donde han trabajado
    y crear reseñas pendientes automáticamente.
    """
    
    # ===== CAMPOS DE RELACIÓN =====
    user_profile = models.ForeignKey(
        'accounts.UserProfile', 
        on_delete=models.CASCADE,
        verbose_name="Perfil de usuario",
        related_name="work_history"
    )
    
    company = models.ForeignKey(
        'companies.Company', 
        on_delete=models.CASCADE,
        verbose_name="Empresa",
        related_name="work_history"
    )
    
    # ===== CAMPOS BÁSICOS =====
    job_title = models.CharField(
        max_length=200, 
        verbose_name="Cargo o puesto",
        help_text="Título del trabajo o puesto que desempeñaste"
    )
    
    start_date = models.DateField(
        verbose_name="Fecha de inicio",
        help_text="Fecha en que comenzaste a trabajar en esta empresa"
    )
    
    end_date = models.DateField(
        verbose_name="Fecha de finalización",
        help_text="Fecha en que terminaste de trabajar (deja vacío si aún trabajas aquí)",
        null=True,
        blank=True
    )
    
    # ===== CAMPOS DE ESTADO =====
    is_current_job = models.BooleanField(
        default=False,
        verbose_name="Trabajo actual",
        help_text="Indica si actualmente trabajas en esta empresa"
    )
    
    has_review_pending = models.BooleanField(
        default=False,
        verbose_name="Reseña pendiente",
        help_text="Indica si hay una reseña pendiente para esta experiencia laboral"
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
    def create_pending_review(self):
        """Crea automáticamente una reseña pendiente para esta experiencia laboral"""
        if not self.has_review_pending:
            from reviews.models import PendingReview
            PendingReview.objects.create(
                user_profile=self.user_profile,
                company=self.company,
                job_title=self.job_title,
                participation_date=self.start_date
            )
            self.has_review_pending = True
            self.save()
    
    def __str__(self):
        """Representación en string del modelo"""
        return f"{self.user_profile.user.username} - {self.company.name} ({self.job_title})"
    
    class Meta:
        """Configuración del modelo"""
        verbose_name = "Historial Laboral"
        verbose_name_plural = "Historiales Laborales"
        ordering = ['-start_date']  # Ordenar por fecha de inicio (más reciente primero)
        unique_together = ['user_profile', 'company', 'job_title']  # Evitar duplicados