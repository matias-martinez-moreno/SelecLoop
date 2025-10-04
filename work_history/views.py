# =============================================================================
# VISTAS DE LA APLICACIÓN WORK_HISTORY - SelecLoop
# =============================================================================
# Este archivo contiene las vistas relacionadas con historial laboral
#
# Vistas principales:
# - work_history_view: Ver historial laboral del usuario
# - add_work_history_view: Agregar nueva experiencia laboral
# =============================================================================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import WorkHistory
from .forms import WorkHistoryForm
from achievements.models import Achievement, UserAchievement


def check_and_award_achievements(user_profile):
    """
    Verifica y otorga logros automáticamente al usuario.
    Se ejecuta después de acciones importantes como agregar historial laboral.
    """
    try:
        # Obtener logros activos
        active_achievements = Achievement.objects.filter(is_active=True)
        
        # Obtener logros ya obtenidos por el usuario
        user_achievements = UserAchievement.objects.filter(user_profile=user_profile).values_list('achievement_id', flat=True)
        
        # Contar experiencias laborales
        work_history_count = WorkHistory.objects.filter(user_profile=user_profile).count()
        
        new_achievements = []
        
        for achievement in active_achievements:
            # Saltar si ya tiene el logro
            if achievement.id in user_achievements:
                continue
                
            # Verificar criterios según el tipo de logro
            if achievement.achievement_type == 'work_history' and work_history_count >= achievement.required_value:
                new_achievements.append(achievement)
        
        # Otorgar nuevos logros
        for achievement in new_achievements:
            UserAchievement.objects.create(
                user_profile=user_profile,
                achievement=achievement
            )
            
        return new_achievements
        
    except Exception as e:
        print(f"Error al verificar logros: {e}")
        return []


@login_required
def work_history_view(request):
    """Vista para gestionar el historial laboral del usuario"""
    if request.user.profile.role != 'candidate':
        messages.error(request, '❌ Solo los candidatos pueden gestionar su historial laboral.')
        return redirect('dashboard')
    
    # Obtener historial laboral del usuario
    work_history = WorkHistory.objects.filter(
        user_profile=request.user.profile
    ).select_related('company').order_by('-start_date')
    
    context = {
        'work_history': work_history,
        'title': 'Mi Historial Laboral'
    }
    
    return render(request, 'core/work_history.html', context)


@login_required
def add_work_history_view(request):
    """Vista para agregar una nueva experiencia laboral"""
    if request.user.profile.role != 'candidate':
        messages.error(request, '❌ Solo los candidatos pueden agregar experiencias laborales.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = WorkHistoryForm(request.POST)
        if form.is_valid():
            try:
                # Crear la experiencia laboral
                work_history = form.save(commit=False)
                work_history.user_profile = request.user.profile
                work_history.save()
                
                # Crear reseña pendiente automáticamente
                work_history.create_pending_review()
                
                # Verificar y otorgar logros
                new_achievements = check_and_award_achievements(request.user.profile)
                
                messages.success(request, f'✅ Experiencia laboral agregada exitosamente para {work_history.company.name}. Se ha creado una reseña pendiente.')
                
                # Mostrar logros obtenidos
                if new_achievements:
                    for achievement in new_achievements:
                        messages.success(request, f'🏆 ¡Nuevo logro desbloqueado! {achievement.name} - {achievement.description}')
                
                return redirect('work_history')
            except Exception as e:
                messages.error(request, f'❌ Error al agregar experiencia laboral: {str(e)}. Verifica que todos los datos sean correctos e intenta nuevamente.')
        else:
            messages.error(request, '❌ Por favor, corrige los errores en el formulario.')
    else:
        form = WorkHistoryForm()
    
    # Obtener empresas existentes para autocompletado
    from companies.models import Company
    existing_companies = Company.objects.filter(is_active=True).order_by('name')
    
    context = {
        'form': form,
        'title': 'Agregar Experiencia Laboral',
        'existing_companies': existing_companies
    }
    
    return render(request, 'core/add_work_history.html', context)