# =============================================================================
# VISTAS DE LA APLICACIÓN REVIEWS - SelecLoop
# =============================================================================
# Este archivo contiene las vistas relacionadas con reseñas
#
# Vistas principales:
# - create_review_view: Crear una nueva reseña
# - my_reviews_view: Ver las reseñas del usuario
# =============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
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
        
        # Contar solo reseñas APROBADAS del usuario (las rechazadas no cuentan para logros)
        review_count = Review.objects.filter(user_profile=user_profile, status='approved').count()
        
        # Contar empresas únicas en reseñas APROBADAS
        company_count = Review.objects.filter(user_profile=user_profile, status='approved').values('company').distinct().count()
        
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
        # Establecer el queryset antes de crear el formulario
        company_id = request.GET.get('company')
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
                form = ReviewForm(request.POST, request.FILES)
                form.fields['company'].queryset = Company.objects.filter(id=company_id)
            except Company.DoesNotExist:
                form = ReviewForm(request.POST, request.FILES)
                form.fields['company'].queryset = Company.objects.filter(is_active=True)
        else:
            form = ReviewForm(request.POST, request.FILES)
            form.fields['company'].queryset = Company.objects.filter(is_active=True)
        if form.is_valid():
            try:
                # Crear reseña
                review = form.save(commit=False)
                review.user_profile = request.user.profile
                review.is_approved = False
                # No establecer status aquí - el método save() del modelo lo manejará con la verificación automática
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
                
                # Mensaje según el estado de la reseña
                if review.status == 'approved':
                    messages.success(request, f'✅ ¡Reseña aprobada exitosamente! Tu reseña para {company.name} ha sido publicada.')
                    # Solo otorgar logros si la reseña fue APROBADA
                    new_achievements = check_and_award_achievements(request.user.profile)
                    # Mostrar logros obtenidos
                    if new_achievements:
                        for achievement in new_achievements:
                            messages.success(request, f'🏆 ¡Nuevo logro desbloqueado! {achievement.name} - {achievement.description}')
                elif review.status == 'rejected':
                    messages.warning(request, f'⚠️ Tu reseña para {company.name} fue rechazada. Razón: {review.verification_reason}')
                    # NO otorgar logros si la reseña fue rechazada
                else:
                    messages.info(request, f'ℹ️ Tu reseña para {company.name} ha sido enviada.')
                
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
        # Pre-seleccionar empresa y cargo
        initial_data = {}
        company_id = request.GET.get('company')
        job_title = request.GET.get('job_title')
        
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
                initial_data['company'] = company  # Usar el objeto completo, no el ID
                
                # Si hay un cargo específico, preseleccionarlo también
                if job_title:
                    initial_data['job_title'] = job_title
                
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


@login_required
def delete_review_view(request, review_id):
    """Vista para eliminar una reseña del usuario"""
    if request.user.profile.role != 'candidate':
        messages.error(request, 'Acceso no autorizado.')
        return redirect('dashboard')
    
    try:
        # Obtener la reseña y verificar que pertenece al usuario
        review = Review.objects.get(
            id=review_id,
            user_profile=request.user.profile
        )
        
        # Eliminar la reseña
        company_name = review.company.name
        review.delete()
        
        messages.success(request, f'✅ Reseña de {company_name} eliminada exitosamente.')
        
    except Review.DoesNotExist:
        messages.error(request, '❌ La reseña no existe o no tienes permisos para eliminarla.')
    
    return redirect('my_reviews')


@login_required
def rejected_reviews_view(request, company_id):
    """Vista para que las empresas vean las reseñas rechazadas"""
    company = get_object_or_404(Company, id=company_id)
    
    # Verificar que el usuario es representante de la empresa o staff
    # Cualquier company_rep o staff puede ver las reseñas rechazadas de cualquier empresa
    if not (request.user.is_staff or request.user.profile.role == 'company_rep'):
        messages.error(request, '❌ No tienes permisos para ver las reseñas rechazadas.')
        return redirect('dashboard')
    
    # Obtener reseñas rechazadas
    rejected_reviews = Review.objects.filter(
        company=company,
        status='rejected'
    ).select_related('user_profile__user').order_by('-submission_date')
    
    # Paginación
    paginator = Paginator(rejected_reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_rejected = rejected_reviews.count()
    total_approved = Review.objects.filter(company=company, status='approved').count()
    
    context = {
        'company': company,
        'rejected_reviews': page_obj,
        'total_rejected': total_rejected,
        'total_approved': total_approved,
    }
    
    return render(request, 'reviews/rejected_reviews.html', context)