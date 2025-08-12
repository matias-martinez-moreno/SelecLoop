# core/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.root_redirect_view, name='root_redirect'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('mi-empresa/', views.company_dashboard_view, name='company_dashboard'), # ¡Debe existir!

    path('empresas/<int:pk>/', views.company_detail_view, name='company_detail'),
    path('crear-reseña/', views.create_review_view, name='create_review'),
    path('mis-reseñas/', views.my_reviews_view, name='my_reviews'),
    path('mi-perfil/', views.profile_view, name='my_profile'),
]