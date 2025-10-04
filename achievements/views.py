# =============================================================================
# VISTAS DE LA APLICACIÓN ACHIEVEMENTS - SelecLoop
# =============================================================================
# Este archivo contiene las vistas relacionadas con logros
#
# Vistas principales:
# - achievements_view: Ver logros del usuario
# =============================================================================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Achievement, UserAchievement
from reviews.models import Review
from work_history.models import WorkHistory


@login_required
def achievements_view(request):
    """Vista para mostrar los logros del usuario"""
    if request.user.profile.role != 'candidate':
        messages.error(request, '❌ Solo los candidatos pueden ver sus logros.')
        return redirect('dashboard')
    
    user_profile = request.user.profile
    
    # Obtener logros obtenidos por el usuario
    user_achievements = UserAchievement.objects.filter(
        user_profile=user_profile
    ).select_related('achievement').order_by('-earned_at')
    
    # Obtener todos los logros disponibles
    all_achievements = Achievement.objects.filter(is_active=True).order_by('achievement_type', 'required_value')
    
    # Obtener IDs de logros ya obtenidos
    earned_achievement_ids = user_achievements.values_list('achievement_id', flat=True)
    
    # Separar logros obtenidos y no obtenidos
    earned_achievements = [ua.achievement for ua in user_achievements]
    unearned_achievements = [achievement for achievement in all_achievements if achievement.id not in earned_achievement_ids]
    
    # Estadísticas del usuario
    total_reviews = Review.objects.filter(user_profile=user_profile).count()
    total_companies = Review.objects.filter(user_profile=user_profile).values('company').distinct().count()
    total_work_history = WorkHistory.objects.filter(user_profile=user_profile).count()
    
    context = {
        'earned_achievements': earned_achievements,
        'unearned_achievements': unearned_achievements,
        'total_achievements': all_achievements.count(),
        'earned_count': user_achievements.count(),
        'user_stats': {
            'total_reviews': total_reviews,
            'total_companies': total_companies,
            'total_work_history': total_work_history,
        },
        'title': 'Mis Logros'
    }
    
    return render(request, 'core/achievements.html', context)