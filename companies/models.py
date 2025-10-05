# =============================================================================
# MODELOS DE LA APLICACIÓN COMPANIES - SelecLoop
# =============================================================================
# Este archivo define los modelos relacionados con empresas
#
# Modelos:
# - Company: Información de empresas con datos geo-localizados
# =============================================================================

from django.db import models


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
    
    logo = models.ImageField(
        verbose_name="Logo",
        help_text="Logo de la empresa",
        upload_to="company_logos/",
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