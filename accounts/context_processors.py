# =============================================================================
# CONTEXT PROCESSORS PARA ACCOUNTS - SelecLoop
# =============================================================================
# Este archivo contiene context processors para agregar datos al contexto global
# =============================================================================

from achievements.models import UserAchievement
from reviews.models import Review


def user_badge(request):
    """
    Context processor que agrega el badge del usuario al contexto global.
    """
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        user_profile = request.user.profile
        
        if user_profile.role == 'candidate':
            try:
                achievement_count = UserAchievement.objects.filter(user_profile=user_profile).count()
                total_reviews = Review.objects.filter(user_profile=user_profile).count()
                
                # Determinar badge basado en logros y reseñas
                if achievement_count >= 10 or total_reviews >= 20:
                    return {
                        'user_badge': {
                            'name': 'Leyenda',
                            'icon': 'fas fa-crown',
                            'color': 'warning',
                            'bg_color': 'bg-warning',
                            'text_color': 'text-dark'
                        }
                    }
                elif achievement_count >= 6 or total_reviews >= 10:
                    return {
                        'user_badge': {
                            'name': 'Maestro',
                            'icon': 'fas fa-trophy',
                            'color': 'warning',
                            'bg_color': 'bg-warning',
                            'text_color': 'text-dark'
                        }
                    }
                elif achievement_count >= 3 or total_reviews >= 5:
                    return {
                        'user_badge': {
                            'name': 'Experto',
                            'icon': 'fas fa-star',
                            'color': 'info',
                            'bg_color': 'bg-info',
                            'text_color': 'text-white'
                        }
                    }
                elif achievement_count >= 1 or total_reviews >= 1:
                    return {
                        'user_badge': {
                            'name': 'Novato',
                            'icon': 'fas fa-seedling',
                            'color': 'success',
                            'bg_color': 'bg-success',
                            'text_color': 'text-white'
                        }
                    }
                else:
                    return {
                        'user_badge': {
                            'name': 'Principiante',
                            'icon': 'fas fa-circle',
                            'color': 'secondary',
                            'bg_color': 'bg-secondary',
                            'text_color': 'text-white'
                        }
                    }
            except Exception:
                pass
    
    return {'user_badge': None}

