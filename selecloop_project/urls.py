# ===== URLs PRINCIPALES DEL PROYECTO SELECLOOP =====
# Este archivo define las rutas principales de la aplicación web
# y conecta las URLs con las vistas correspondientes

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static 

# ===== PATRONES DE URL =====
urlpatterns = [
    # Panel de administración de Django
    path('admin/', admin.site.urls),
    
    # Incluye todas las URLs de la aplicación 'core'
    # Las URLs específicas están definidas en core/urls.py
    path('', include('core.urls')),
]

# ===== CONFIGURACIÓN PARA DESARROLLO =====
# Solo en modo DEBUG, servir archivos de media y estáticos
if settings.DEBUG:
    # Servir archivos de media (imágenes subidas por usuarios)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Servir archivos estáticos (CSS, JS, imágenes del proyecto)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)