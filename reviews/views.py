# =============================================================================
# VISTAS DE LA APLICACIÓN REVIEWS - SelecLoop
# =============================================================================
# Este archivo contiene las vistas relacionadas con reseñas
#
# Vistas principales:
# - create_review_view: Crear una nueva reseña
# - my_reviews_view: Ver las reseñas del usuario
# =============================================================================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Review, PendingReview
from .forms import ReviewForm
from accounts.models import OnboardingStatus
from achievements.models import Achievement, UserAchievement
from work_history.models import WorkHistory
from companies.models import Company


def check_and_award_achievements(user_profile):
    """
    Verifica y otorga logros automáticamente al usuario.
    Se ejecuta después de acciones importantes como crear reseñas.
    """
    try:
        # Obtener logros activos
        active_achievements = Achievement.objects.filter(is_active=True)
        
        # Obtener logros ya obtenidos por el usuario
        user_achievements = UserAchievement.objects.filter(user_profile=user_profile).values_list('achievement_id', flat=True)
        
        # Contar reseñas del usuario
        review_count = Review.objects.filter(user_profile=user_profile).count()
        
        # Contar empresas únicas en reseñas
        company_count = Review.objects.filter(user_profile=user_profile).values('company').distinct().count()
        
        # Contar experiencias laborales
        work_history_count = WorkHistory.objects.filter(user_profile=user_profile).count()
        
        new_achievements = []
        
        for achievement in active_achievements:
            # Saltar si ya tiene el logro
            if achievement.id in user_achievements:
                continue
                
            # Verificar criterios según el tipo de logro
            if achievement.achievement_type == 'first_review' and review_count >= 1:
                new_achievements.append(achievement)
            elif achievement.achievement_type == 'review_count' and review_count >= achievement.required_value:
                new_achievements.append(achievement)
            elif achievement.achievement_type == 'company_count' and company_count >= achievement.required_value:
                new_achievements.append(achievement)
            elif achievement.achievement_type == 'work_history' and work_history_count >= achievement.required_value:
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
def create_review_view(request):
    """Vista para crear una nueva reseña"""
    if request.user.profile.role != 'candidate':
        messages.error(request, '❌ Solo los candidatos pueden crear reseñas. Si eres empresa o staff, usa las funciones correspondientes.')
        return redirect('dashboard')
    
    # Obtener empresas con reseñas pendientes (del sistema anterior)
    pending_companies = PendingReview.objects.filter(
        user_profile=request.user.profile,
        is_reviewed=False
    ).select_related('company')
    
    # Obtener empresas del historial laboral con reseñas pendientes
    work_history_pending = WorkHistory.objects.filter(
        user_profile=request.user.profile,
        has_review_pending=True
    ).select_related('company')
    
    # Combinar ambas fuentes de reseñas pendientes
    all_pending_companies = list(pending_companies) + list(work_history_pending)
    
    # Permitir crear reseñas de cualquier empresa (nuevo flujo)
    available_companies = Company.objects.filter(is_active=True)
    if not available_companies.exists():
        messages.warning(request, '⚠️ No hay empresas disponibles para crear reseñas.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Crear reseña
                review = form.save(commit=False)
                review.user_profile = request.user.profile
                review.status = 'pending'
                review.is_approved = False
                review.save()
                
                # Marcar pendiente como completada (sistema anterior)
                company = form.cleaned_data['company']
                pending_review = PendingReview.objects.filter(
                    user_profile=request.user.profile,
                    company=company,
                    is_reviewed=False
                ).first()
                
                if pending_review:
                    pending_review.is_reviewed = True
                    pending_review.save()
                
                # Marcar la reseña pendiente del historial laboral como completada
                work_history = WorkHistory.objects.filter(
                    user_profile=request.user.profile,
                    company=company,
                    has_review_pending=True
                ).first()
                
                if work_history:
                    work_history.has_review_pending = False
                    work_history.save()
                
                # Actualizar onboarding
                if hasattr(request.user, 'profile'):
                    onboarding_status, created = OnboardingStatus.objects.get_or_create(
                        user_profile=request.user.profile,
                        defaults={
                            'has_participated_in_selection': True,
                            'onboarding_completed': True,
                            'last_onboarding_date': timezone.now(),
                        },
                    )
                    onboarding_status.detect_participation_status()
                
                # Verificar y otorgar logros
                new_achievements = check_and_award_achievements(request.user.profile)
                
                # Mensaje especial si era una reseña pendiente
                if pending_review:
                    messages.success(request, f'🎉 ¡Reseña completada exitosamente! Has completado tu reseña para {company.name}. Ahora puedes acceder a todas las empresas del sistema.')
                else:
                    messages.success(request, '¡Reseña enviada exitosamente! 🎉 Tu reseña está pendiente de aprobación y será revisada por nuestro equipo.')
                
                # Mostrar logros obtenidos
                if new_achievements:
                    for achievement in new_achievements:
                        messages.success(request, f'🏆 ¡Nuevo logro desbloqueado! {achievement.name} - {achievement.description}')
                
                return redirect('my_reviews')
                
            except Exception as e:
                messages.error(request, f'❌ Error al guardar la reseña: {str(e)}. Por favor, intenta nuevamente o contacta al administrador si el problema persiste.')
        else:
            # Mensajes de error más específicos y útiles
            error_messages = {
                'company': 'Debes seleccionar una empresa válida.',
                'job_title': 'El cargo es obligatorio. Ejemplo: "Desarrollador Frontend", "Analista de Datos".',
                'modality': 'Debes seleccionar la modalidad de trabajo (Presencial, Remoto o Híbrido).',
                'communication_rating': 'Debes calificar la comunicación durante el proceso.',
                'difficulty_rating': 'Debes calificar la dificultad del proceso de selección.',
                'response_time_rating': 'Debes calificar el tiempo de respuesta de la empresa.',
                'overall_rating': 'Debes dar una calificación general del 1 al 5.',
                'pros': 'Los aspectos positivos son obligatorios. Describe qué te gustó del proceso.',
                'cons': 'Los aspectos a mejorar son obligatorios. Describe qué podría mejorar.',
                'image': 'El archivo de imagen debe ser válido (JPG, PNG). Tamaño máximo recomendado: 5MB.'
            }
            
            for field, errors in form.errors.items():
                field_name = error_messages.get(field, field.replace('_', ' ').title())
                for error in errors:
                    messages.error(request, f'❌ {field_name}: {error}')
    else:
        # Pre-seleccionar empresa
        initial_data = {}
        company_id = request.GET.get('company')
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
                initial_data['company'] = company.id  # Usar el ID, no el objeto
                # Si hay una empresa específica, solo mostrar esa empresa
                form = ReviewForm(initial=initial_data)
                form.fields['company'].queryset = Company.objects.filter(id=company_id)
            except Company.DoesNotExist:
                form = ReviewForm()
                form.fields['company'].queryset = Company.objects.filter(is_active=True)
        else:
            # Si no hay empresa específica, mostrar todas las empresas activas
            form = ReviewForm()
            form.fields['company'].queryset = Company.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'pending_companies': all_pending_companies,
    }
    
    return render(request, 'core/create_review.html', context)


@login_required
def my_reviews_view(request):
    """Vista para mostrar las reseñas del usuario"""
    if request.user.profile.role != 'candidate':
        messages.error(request, 'Acceso no autorizado.')
        return redirect('dashboard')
    
    # Obtener reseñas
    user_reviews = Review.objects.filter(
        user_profile=request.user.profile
    ).select_related('company').order_by('-submission_date')
    
    pending_reviews = PendingReview.objects.filter(
        user_profile=request.user.profile,
        is_reviewed=False
    ).select_related('company')
    
    context = {
        'user_reviews': user_reviews,
        'pending_reviews': pending_reviews,
    }
    
    return render(request, 'core/my_reviews.html', context)