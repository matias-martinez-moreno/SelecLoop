# ===== URLs DE LA APLICACIÓN COMMON =====
# Este archivo define las rutas para utilidades comunes (SEO)

from django.urls import path
from . import views

# ===== PATRONES DE URL =====
urlpatterns = [
    # ===== VISTAS SEO =====
    # Robots.txt para motores de búsqueda
    path('robots.txt', views.robots_txt_view, name='robots_txt'),

    # Sitemap.xml para motores de búsqueda
    path('sitemap.xml', views.sitemap_xml_view, name='sitemap'),
]
