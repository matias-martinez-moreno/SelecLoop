# ===== URLs DE LA APLICACIÓN ACHIEVEMENTS =====
# Este archivo define las rutas relacionadas con logros

from django.urls import path
from . import views

# ===== PATRONES DE URL =====
urlpatterns = [
    # ===== SISTEMA DE LOGROS =====
    # Ver logros del usuario
    path('achievements/', views.achievements_view, name='achievements'),
]
