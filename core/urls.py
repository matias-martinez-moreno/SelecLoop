# ===== URLs DE LA APLICACIÓN CORE =====
# Este archivo define las rutas principales y coordina las URLs de todas las apps
# Las URLs específicas han sido movidas a sus respectivas aplicaciones

from django.urls import path, include
from . import views

# ===== PATRONES DE URL =====
urlpatterns = [
    # ===== PÁGINAS PRINCIPALES =====
    # Página de inicio - redirige según el rol del usuario
    path('', views.root_redirect_view, name='root'),
    
    # Dashboard principal para candidatos
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # ===== INCLUIR URLs DE OTRAS APPS =====
    # URLs de autenticación y perfiles
    path('', include('accounts.urls')),
    
    # URLs de empresas
    path('', include('companies.urls')),
    
    # URLs de reseñas
    path('', include('reviews.urls')),
    
    # URLs de historial laboral
    path('', include('work_history.urls')),
    
    # URLs de logros
    path('', include('achievements.urls')),
    
    # URLs de utilidades comunes (SEO)
    path('', include('common.urls')),

    # ===== VISTAS DEL STAFF =====
    # (Eliminadas - ahora se usa moderación automática con machine learning)
    # Export CSV de reseñas por empresa (solo company_rep/staff)
    path('company/<int:company_id>/export-reviews.csv', views.export_company_reviews_csv, name='export_company_reviews_csv'),

    # ===== VISTAS SEO =====
    # Robots.txt para motores de búsqueda
    path('robots.txt', views.robots_txt_view, name='robots_txt'),

    # Sitemap.xml para motores de búsqueda
    path('sitemap.xml', views.sitemap_xml_view, name='sitemap'),
]