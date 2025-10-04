# =============================================================================
# MODELOS DE LA APLICACIÓN ACHIEVEMENTS - SelecLoop
# =============================================================================
# Este archivo define los modelos relacionados con logros y gamificación
#
# Modelos:
# - Achievement: Logros disponibles en el sistema
# - UserAchievement: Logros obtenidos por usuarios
# =============================================================================

from django.db import models


# ===== MODELO: LOGROS Y RECOMPENSAS =====
class Achievement(models.Model):
    """
    Modelo que representa un logro o recompensa que puede obtener un usuario.
    Sistema de gamificación para motivar la participación.
    """
    
    # ===== CAMPOS BÁSICOS =====
    name = models.CharField(
        max_length=100,
        verbose_name="Nombre del logro",
        help_text="Nombre del logro (ej: 'Primera Reseña', 'Experto en Reseñas')"
    )
    
    description = models.TextField(
        verbose_name="Descripción",
        help_text="Descripción detallada del logro y cómo obtenerlo"
    )
    
    # ===== CAMPOS DE ICONO Y COLOR =====
    icon = models.CharField(
        max_length=50,
        default="fas fa-star",
        verbose_name="Icono",
        help_text="Clase de FontAwesome para el icono (ej: 'fas fa-star', 'fas fa-trophy')"
    )
    
    color = models.CharField(
        max_length=20,
        default="gold",
        verbose_name="Color",
        help_text="Color del logro (gold, silver, bronze, blue, green, red)"
    )
    
    # ===== CAMPOS DE CRITERIOS =====
    ACHIEVEMENT_TYPES = [
        ('first_review', 'Primera Reseña'),
        ('review_count', 'Cantidad de Reseñas'),
        ('company_count', 'Cantidad de Empresas'),
        ('work_history', 'Historial Laboral'),
        ('special', 'Especial'),
    ]
    
    achievement_type = models.CharField(
        max_length=20,
        choices=ACHIEVEMENT_TYPES,
        verbose_name="Tipo de logro",
        help_text="Tipo de logro que determina cómo se otorga"
    )
    
    required_value = models.IntegerField(
        default=1,
        verbose_name="Valor requerido",
        help_text="Valor necesario para obtener el logro (ej: 5 reseñas, 3 empresas)"
    )
    
    # ===== CAMPOS DE ESTADO =====
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el logro está disponible para obtener"
    )
    
    # ===== CAMPOS DE FECHA =====
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    # ===== MÉTODOS =====
    def __str__(self):
        """Representación en string del modelo"""
        return self.name
    
    class Meta:
        """Configuración del modelo"""
        verbose_name = "Logro"
        verbose_name_plural = "Logros"
        ordering = ['achievement_type', 'required_value']


# ===== MODELO: LOGROS DE USUARIO =====
class UserAchievement(models.Model):
    """
    Modelo que representa los logros obtenidos por un usuario.
    Relación many-to-many entre UserProfile y Achievement.
    """
    
    # ===== CAMPOS DE RELACIÓN =====
    user_profile = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.CASCADE,
        verbose_name="Perfil de usuario",
        related_name="achievements"
    )
    
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        verbose_name="Logro",
        related_name="user_achievements"
    )
    
    # ===== CAMPOS DE FECHA =====
    earned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de obtención"
    )
    
    # ===== MÉTODOS =====
    def __str__(self):
        """Representación en string del modelo"""
        return f"{self.user_profile.user.username} - {self.achievement.name}"
    
    class Meta:
        """Configuración del modelo"""
        verbose_name = "Logro de Usuario"
        verbose_name_plural = "Logros de Usuario"
        ordering = ['-earned_at']
        unique_together = ['user_profile', 'achievement']  # Evitar duplicados