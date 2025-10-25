# ===== URLs DE LA APLICACIÓN REVIEWS =====
# Este archivo define las rutas relacionadas con reseñas

from django.urls import path
from . import views

# ===== PATRONES DE URL =====
urlpatterns = [
    # ===== GESTIÓN DE RESEÑAS =====
    # Crear una nueva reseña
    path('create-review/', views.create_review_view, name='create_review'),
    
    # Ver las reseñas del usuario actual
    path('my-reviews/', views.my_reviews_view, name='my_reviews'),
    
    # Eliminar una reseña
    path('delete-review/<int:review_id>/', views.delete_review_view, name='delete_review'),
    
    # Ver reseñas rechazadas de una empresa
    path('rejected/<int:company_id>/', views.rejected_reviews_view, name='rejected_reviews'),
]
