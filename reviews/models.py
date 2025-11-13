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
    
    # ===== CAMPOS DE VERIFICACIÓN AUTOMÁTICA =====
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Verificada",
        help_text="Indica si la reseña ha sido verificada por el sistema automático"
    )
    
    verification_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Razón de verificación",
        help_text="Razón por la cual la reseña fue aprobada o rechazada"
    )
    
    verification_confidence = models.FloatField(
        default=0.0,
        verbose_name="Confianza de verificación",
        help_text="Nivel de confianza del sistema de verificación (0.0 a 1.0)"
    )
    
    verification_category = models.CharField(
        max_length=20,
        choices=[
            ('appropriate', 'Apropiada'),
            ('toxic', 'Tóxica'),
            ('hate_speech', 'Discurso de Odio'),
            ('off_topic', 'Fuera de Lugar'),
            ('spam', 'Spam'),
            ('insufficient_content', 'Contenido Insuficiente'),
            ('error', 'Error en Verificación')
        ],
        default='appropriate',
        verbose_name="Categoría de verificación",
        help_text="Categoría asignada por el sistema de verificación"
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
    def save(self, *args, **kwargs):
        """Método save personalizado para verificación automática"""
        # Verificar automáticamente al guardar si no está verificada
        # Verificar si hay contenido para analizar
        has_content = bool(
            (self.pros and self.pros.strip()) or 
            (self.cons and self.cons.strip()) or 
            (self.interview_questions and self.interview_questions.strip())
        )
        
        # SIEMPRE verificar si no está verificada y hay contenido
        if not self.is_verified and has_content:
            # Log para confirmar que se va a verificar
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("🔍 CONDICIÓN DE VERIFICACIÓN CUMPLIDA - Iniciando verificación...")
            try:
                
                from core.services.review_verification import ReviewVerificationService
                verification_service = ReviewVerificationService()
                
                # Combinar todo el contenido de la reseña para verificar
                # Incluir pros, cons e interview_questions (todos son obligatorios)
                pros_text = (self.pros or '').strip()
                cons_text = (self.cons or '').strip()
                interview_text = (self.interview_questions or '').strip()
                content_to_verify = f"{pros_text} {cons_text} {interview_text}".strip()
                
                logger.warning("=" * 80)
                logger.warning("📝 ENVIANDO RESEÑA A VERIFICACIÓN")
                logger.warning(f"   Empresa: {self.company.name if self.company else 'N/A'}")
                logger.warning(f"   Usuario: {self.user_profile.user.username if self.user_profile else 'N/A'}")
                logger.warning(f"   Pros: {pros_text[:50]}..." if pros_text else "   Pros: (vacío)")
                logger.warning(f"   Contras: {cons_text[:50]}..." if cons_text else "   Contras: (vacío)")
                logger.warning(f"   Preguntas: {interview_text[:50]}..." if interview_text else "   Preguntas: (vacío)")
                logger.warning(f"   Longitud total del texto: {len(content_to_verify)} caracteres")
                logger.warning(f"   is_verified antes: {self.is_verified}")
                logger.warning("=" * 80)
                
                result = verification_service.verify_review(content_to_verify)
                
                logger.warning("=" * 80)
                logger.warning("📊 RESULTADO DE VERIFICACIÓN")
                logger.warning(f"   ¿Apropiada?: {result['is_appropriate']}")
                logger.warning(f"   Razón: {result['reason']}")
                logger.warning(f"   Confianza: {result['confidence']}")
                logger.warning(f"   Categoría: {result['category']}")
                logger.warning(f"   ¿ML usado?: {result.get('ml_models_used', False)}")
                if 'toxicity_score' in result:
                    logger.warning(f"   Toxicity Score: {result.get('toxicity_score', 0)}")
                if 'sentiment_score' in result:
                    logger.warning(f"   Sentiment Score: {result.get('sentiment_score', 0)} ({result.get('sentiment_label', 'N/A')})")
                logger.warning("=" * 80)
                
                self.is_verified = True
                self.verification_reason = result['reason']
                self.verification_confidence = result['confidence']
                self.verification_category = result['category']
                
                # Determinar status basado en resultado
                if result['is_appropriate']:
                    self.status = 'approved'
                    self.is_approved = True
                    logger.warning(f"✅✅✅ RESEÑA APROBADA: {result['reason']}")
                else:
                    self.status = 'rejected'  # Rechazar automáticamente contenido inapropiado
                    self.is_approved = False
                    logger.warning(f"❌❌❌ RESEÑA RECHAZADA: {result['reason']} (categoría: {result['category']})")
                    
            except Exception as e:
                # Si hay error, aprobar la reseña por defecto para no bloquear contenido legítimo
                import logging
                logger = logging.getLogger(__name__)
                logger.error("=" * 80)
                logger.error("❌❌❌ ERROR EN VERIFICACIÓN DE RESEÑA ❌❌❌")
                logger.error(f"   Error: {str(e)}")
                logger.error(f"   Traceback completo:")
                import traceback
                logger.error(traceback.format_exc())
                logger.error("=" * 80)
                
                self.is_verified = True
                self.verification_reason = f'Error en verificación automática: {str(e)}'
                self.verification_confidence = 0.0
                self.verification_category = 'error'
                self.status = 'approved'  # Aprobar en caso de error para no bloquear contenido legítimo
                self.is_approved = True
                logger.warning("⚠️ Reseña aprobada por defecto debido a error en verificación")
        else:
            # Log cuando NO se ejecuta la verificación
            import logging
            logger = logging.getLogger(__name__)
            if self.is_verified:
                logger.warning(f"⏭️ VERIFICACIÓN OMITIDA: Reseña ya verificada (is_verified={self.is_verified})")
            if not has_content:
                logger.warning(f"⏭️ VERIFICACIÓN OMITIDA: No hay contenido para verificar (pros={bool(self.pros)}, cons={bool(self.cons)}, interview={bool(self.interview_questions)})")
        
        super().save(*args, **kwargs)
    
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