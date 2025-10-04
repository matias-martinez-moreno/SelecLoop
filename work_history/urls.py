# ===== URLs DE LA APLICACIÓN WORK_HISTORY =====
# Este archivo define las rutas relacionadas con historial laboral

from django.urls import path
from . import views

# ===== PATRONES DE URL =====
urlpatterns = [
    # ===== GESTIÓN DE HISTORIAL LABORAL =====
    # Ver historial laboral del usuario
    path('work-history/', views.work_history_view, name='work_history'),
    
    # Agregar nueva experiencia laboral
    path('add-work-history/', views.add_work_history_view, name='add_work_history'),
]
