# =============================================================================
# TEMPLATE TAGS PARA ACCOUNTS - SelecLoop
# =============================================================================
# Este archivo contiene template tags personalizados para la app accounts
# =============================================================================

from django import template
from achievements.models import UserAchievement
from reviews.models import Review

register = template.Library()


@register.simple_tag
def get_user_badge(user_profile):
    """
    Determina el badge del usuario basado en sus logros obtenidos.
    Retorna un diccionario con nombre, icono y color del badge.
    """
    if not user_profile or user_profile.role != 'candidate':
        return None
    
    try:
        achievement_count = UserAchievement.objects.filter(user_profile=user_profile).count()
        total_reviews = Review.objects.filter(user_profile=user_profile).count()
        
        # Determinar badge basado en logros y reseñas
        if achievement_count >= 10 or total_reviews >= 20:
            return {
                'name': 'Leyenda',
                'icon': 'fas fa-crown',
                'color': 'warning',
                'bg_color': 'bg-warning',
                'text_color': 'text-dark'
            }
        elif achievement_count >= 6 or total_reviews >= 10:
            return {
                'name': 'Maestro',
                'icon': 'fas fa-trophy',
                'color': 'warning',
                'bg_color': 'bg-warning',
                'text_color': 'text-dark'
            }
        elif achievement_count >= 3 or total_reviews >= 5:
            return {
                'name': 'Experto',
                'icon': 'fas fa-star',
                'color': 'info',
                'bg_color': 'bg-info',
                'text_color': 'text-white'
            }
        elif achievement_count >= 1 or total_reviews >= 1:
            return {
                'name': 'Novato',
                'icon': 'fas fa-seedling',
                'color': 'success',
                'bg_color': 'bg-success',
                'text_color': 'text-white'
            }
        else:
            return {
                'name': 'Principiante',
                'icon': 'fas fa-circle',
                'color': 'secondary',
                'bg_color': 'bg-secondary',
                'text_color': 'text-white'
            }
    except Exception:
        return None

