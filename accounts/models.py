# =============================================================================
# MODELOS DE LA APLICACIÓN ACCOUNTS - SelecLoop
# =============================================================================
# Este archivo define los modelos relacionados con usuarios y autenticación
#
# Modelos:
# - UserProfile: Perfil extendido de usuario con roles
# - OnboardingStatus: Estado de onboarding de usuarios
# =============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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
        'companies.Company', 
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
    
    city = models.CharField(
        max_length=100,
        verbose_name="Ciudad",
        help_text="Ciudad donde resides",
        blank=True,
        null=True
    )
    
    country = models.CharField(
        max_length=100,
        verbose_name="País",
        help_text="País donde resides",
        blank=True,
        null=True
    )
    
    linkedin_url = models.URLField(
        max_length=200,
        verbose_name="LinkedIn",
        help_text="URL de tu perfil de LinkedIn",
        blank=True,
        null=True
    )
    
    portfolio_url = models.URLField(
        max_length=200,
        verbose_name="Portfolio/Website",
        help_text="URL de tu portfolio o sitio web personal",
        blank=True,
        null=True
    )
    
    years_of_experience = models.PositiveIntegerField(
        verbose_name="Años de experiencia",
        help_text="Años de experiencia profesional",
        blank=True,
        null=True
    )
    
    specialization = models.CharField(
        max_length=200,
        verbose_name="Área de especialización",
        help_text="Tu área de especialización profesional (ej: Desarrollo Web, Marketing Digital)",
        blank=True,
        null=True
    )
    
    languages = models.CharField(
        max_length=200,
        verbose_name="Idiomas",
        help_text="Idiomas que manejas (ej: Español, Inglés, Francés)",
        blank=True,
        null=True
    )
    
    AVAILABILITY_CHOICES = [
        ('available', 'Disponible'),
        ('not_available', 'No disponible'),
        ('actively_looking', 'Buscando activamente'),
    ]
    
    availability_status = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        verbose_name="Disponibilidad",
        help_text="Tu disponibilidad laboral actual",
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


# ===== SIGNAL: CREAR PERFIL AUTOMÁTICAMENTE =====
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crea automáticamente un perfil cuando se crea un usuario"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guarda el perfil cuando se guarda el usuario"""
    if hasattr(instance, 'profile'):
        instance.profile.save()