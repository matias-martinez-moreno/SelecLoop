# =============================================================================
# VISTAS DE LA APLICACIÓN COMMON - SelecLoop
# =============================================================================
# Este archivo contiene vistas de utilidades comunes
#
# Vistas principales:
# - robots_txt_view: Robots.txt para SEO
# - sitemap_xml_view: Sitemap.xml para SEO
# =============================================================================

from django.http import HttpResponse
from django.template.loader import render_to_string
from companies.models import Company


def robots_txt_view(request):
    """
    Vista para servir el archivo robots.txt - Guía para motores de búsqueda

    Genera dinámicamente el archivo robots.txt que indica a los motores de búsqueda:
    - Qué páginas pueden indexar
    - Qué páginas deben evitar
    - Ubicación del sitemap.xml

    SEO Benefits:
    - Controla qué contenido indexan los motores de búsqueda
    - Evita indexación de áreas sensibles (admin, staff)
    - Referencia al sitemap para mejor crawling
    """
    # Obtener el protocolo y dominio para URLs absolutas
    protocol = 'https' if request.is_secure() else 'http'
    domain = request.get_host()

    context = {
        'protocol': protocol,
        'domain': domain,
    }

    robots_content = render_to_string('core/robots.txt', context)
    return HttpResponse(robots_content, content_type='text/plain')


def sitemap_xml_view(request):
    """
    Vista para servir el archivo sitemap.xml - Mapa del sitio para SEO

    Genera dinámicamente el sitemap XML que incluye:
    - Página principal y páginas estáticas
    - Todas las empresas activas con sus URLs
    - Metadatos de última modificación y prioridad

    SEO Benefits:
    - Ayuda a motores de búsqueda a encontrar todas las páginas
    - Proporciona información sobre frecuencia de actualización
    - Prioriza páginas importantes para crawling
    - Incluye datos geo-localizados para SEO local
    """
    # Obtener todas las empresas activas para incluir en sitemap
    companies = Company.objects.filter(is_active=True).order_by('name')

    # Obtener el protocolo y dominio para URLs absolutas
    protocol = 'https' if request.is_secure() else 'http'
    domain = request.get_host()

    context = {
        'companies': companies,
        'protocol': protocol,
        'domain': domain,
    }

    sitemap_content = render_to_string('core/sitemap.xml', context)
    return HttpResponse(sitemap_content, content_type='application/xml')