# =============================================================================
# VISTAS DE LA APLICACIÓN CORE - SelecLoop
# =============================================================================
# Este archivo contiene toda la lógica de negocio de SelecLoop
# Maneja las peticiones HTTP, procesa datos y renderiza templates
#
# Arquitectura: Patrón MVT (Model-View-Template) de Django
# Patrón: Controller en arquitectura MVC (las views actúan como controllers)
#
# Funcionalidades principales:
# - Autenticación y autorización de usuarios
# - Gestión de reseñas y empresas
# - Dashboards personalizados por rol
# - Estadísticas y analytics con gráficos
# - SEO: Sitemap y robots.txt dinámicos
# - Exportación de datos (CSV)
#
# Vistas principales:
# - dashboard_view: Dashboard principal para candidatos
# - company_detail_view: Detalle de empresa con estadísticas
# - create_review_view: Creación de reseñas
# - SEO views: sitemap_xml_view, robots_txt_view
# =============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Company, UserProfile, Review, OnboardingStatus, PendingReview, WorkHistory, Achievement, UserAchievement
from .forms import ReviewForm, UserCreationForm, ProfileUpdateForm, WorkHistoryForm
from django.db.models.functions import TruncMonth
import json
import io
import base64
# matplotlib removido - ya no se usan gráficos
from django.http import HttpResponse
from datetime import timedelta

# ===== FUNCIONES AUXILIARES =====

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

def is_staff_user(user):
    """Verifica si el usuario es staff"""
    return user.is_authenticated and user.is_staff

# ===== VISTAS DE AUTENTICACIÓN =====

def root_redirect_view(request):
    """Redirige según el rol del usuario"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.role:
            if request.user.profile.role == 'candidate':
                return redirect('dashboard')
            elif request.user.profile.role == 'company_rep':
                return redirect('company_dashboard')
            elif request.user.profile.role == 'staff':
                return redirect('staff_dashboard')
            else:
                return redirect('dashboard')
        elif request.user.is_staff:
            return redirect('staff_dashboard')
        else:
            return redirect('dashboard')
    return redirect('login')


def login_view(request):
    """Vista de login - autentica usuarios y redirige según rol"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Asegurar que el usuario tenga perfil y rol correcto
            try:
                profile = getattr(user, 'profile', None)
                if profile is None:
                    # Determinar rol por defecto
                    if user.is_staff:
                        default_role = 'staff'
                    elif user.username.lower() == 'company':
                        default_role = 'company_rep'
                    else:
                        default_role = 'candidate'
                    UserProfile.objects.create(user=user, role=default_role)
                    profile = user.profile
                else:
                    # Sincronizar rol con el estado del usuario/datos conocidos
                    updated_role = None
                    if user.is_staff and profile.role != 'staff':
                        updated_role = 'staff'
                    elif user.username.lower() == 'company' and profile.role != 'company_rep':
                        updated_role = 'company_rep'
                    if updated_role:
                        profile.role = updated_role
                        profile.save()
            except Exception as e:
                # No bloquear el login por fallo en creación de perfil
                messages.warning(request, f'No se pudo verificar el perfil del usuario: {str(e)}')
            
            # Actualizar onboarding para candidatos
            if hasattr(user, 'profile') and user.profile.role == 'candidate':
                onboarding_status, created = OnboardingStatus.objects.get_or_create(
                    user_profile=user.profile,
                    defaults={
                        'has_participated_in_selection': False,
                        'onboarding_completed': False,
                        'last_onboarding_date': timezone.now(),
                    },
                )
                onboarding_status.detect_participation_status()
                if not onboarding_status.onboarding_completed:
                    onboarding_status.onboarding_completed = True
                    onboarding_status.save()
            
            messages.success(request, f'🎉 ¡Bienvenido de nuevo, {user.username}! Has iniciado sesión correctamente.')
            
            # Redirigir según rol
            if hasattr(user, 'profile') and user.profile.role:
                if user.profile.role == 'candidate':
                    return redirect('dashboard')
                elif user.profile.role == 'company_rep':
                    return redirect('company_dashboard')
                elif user.profile.role == 'staff':
                    return redirect('staff_dashboard')
                else:
                    return redirect('dashboard')
            elif user.is_staff:
                return redirect('staff_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, '❌ Usuario o contraseña incorrectos. Verifica tus credenciales e intenta nuevamente.')
    
    return render(request, 'core/login.html', {'title': 'Iniciar Sesión'})


@login_required
def logout_view(request):
    """Cierra sesión del usuario"""
    logout(request)
    messages.success(request, '👋 Has cerrado sesión exitosamente. ¡Hasta pronto!')
    return redirect('login')

# ===== VISTAS DE DASHBOARD =====

@login_required
def dashboard_view(request):
    """
    Dashboard principal para candidatos - Vista central de SelecLoop

    Esta vista muestra:
    - Lista de empresas disponibles para reseñar
    - Reseñas pendientes del usuario
    - Estadísticas rápidas (empresas, reseñas completadas/pendientes)
    - Filtros por nombre, ciudad, sector y modalidad
    - Estado de acceso a cada empresa

    Funcionalidades SEO/Geo:
    - Filtros por ubicación geográfica
    - Información de ciudad/región en resultados
    - Meta tags dinámicos por búsqueda

    Seguridad:
    - Solo accesible para usuarios con rol 'candidate'
    - Control de acceso basado en reseñas pendientes
    """
    if request.user.profile.role != 'candidate':
        messages.error(request, 'Acceso no autorizado.')
        return redirect('login')
    
    # Parámetros de búsqueda
    search_query = request.GET.get('search', '')
    city_filter = request.GET.get('city', '')
    sector_filter = request.GET.get('sector', '')
    modality_filter = request.GET.get('modality', '')
    
    # Consulta de empresas
    companies = Company.objects.filter(is_active=True)
    
    if search_query:
        companies = companies.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(sector__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(region__icontains=search_query) |
            Q(country__icontains=search_query)
        )
    
    if city_filter:
        companies = companies.filter(location=city_filter)
    
    if sector_filter:
        companies = companies.filter(sector=sector_filter)
    
    if modality_filter:
        # Filtrar empresas que tengan reseñas con la modalidad seleccionada
        companies = companies.filter(reviews__modality=modality_filter).distinct()
    
    # Reseñas del usuario
    pending_reviews = PendingReview.objects.filter(
        user_profile=request.user.profile,
        is_reviewed=False
    ).select_related('company')
    
    completed_reviews = Review.objects.filter(
        user_profile=request.user.profile
    ).exclude(status='rejected')
    
    # Datos para filtros
    cities = Company.objects.filter(is_active=True).values_list('location', flat=True).distinct().order_by('location')
    sectors = Company.objects.filter(is_active=True).values_list('sector', flat=True).distinct().order_by('sector')
    
    # Modalidades disponibles (basadas en las reseñas existentes)
    modalities = Review.objects.values_list('modality', flat=True).distinct().order_by('modality')
    modality_choices = [
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('híbrido', 'Híbrido'),
    ]
    
    # Agregar estado a cada empresa
    for company in companies:
        company.has_pending_review = pending_reviews.filter(company=company).exists()
        company.has_completed_review = completed_reviews.filter(company=company).exists()
    
    context = {
        'companies': companies,
        'pending_reviews': pending_reviews,
        'completed_reviews': completed_reviews,
        'cities': cities,
        'sectors': sectors,
        'modalities': modalities,
        'modality_choices': modality_choices,
        'search_query': search_query,
        'city_filter': city_filter,
        'sector_filter': sector_filter,
        'modality_filter': modality_filter,
        'total_companies': companies.count(),
        'total_reviews': Review.objects.count(),
        'total_candidates': UserProfile.objects.filter(role='candidate').count(),
        'chart_data': {
            'ratings': {},
            'modality': {},
            'status': {},
            'timeline': {}
        }
    }
    
    # Generar datos para gráficos del usuario
    user_reviews = Review.objects.filter(user_profile=request.user.profile)
    if user_reviews.exists():
        # Distribución de calificaciones del usuario
        rating_counts = {}
        for i in range(1, 6):
            count = user_reviews.filter(overall_rating=i).count()
            rating_counts[f'{i} estrella{"s" if i > 1 else ""}'] = count
        context['chart_data']['ratings'] = rating_counts
        
        # Modalidades del usuario
        modality_counts = {}
        for modality, _ in Review.MODALITY_CHOICES:
            count = user_reviews.filter(modality=modality).count()
            if count > 0:
                modality_counts[modality.title()] = count
        context['chart_data']['modality'] = modality_counts
        
        # Estados de reseñas del usuario
        status_counts = {}
        for status, _ in Review.STATUS_CHOICES:
            count = user_reviews.filter(status=status).count()
            if count > 0:
                status_counts[status.title()] = count
        context['chart_data']['status'] = status_counts
        
        # Timeline de reseñas del usuario (últimos 6 meses)
        timeline_data = {}
        for i in range(6):
            month_start = timezone.now() - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            count = user_reviews.filter(
                submission_date__gte=month_start,
                submission_date__lt=month_end
            ).count()
            month_name = month_start.strftime('%b %Y')
            timeline_data[month_name] = count
        context['chart_data']['timeline'] = timeline_data
    
    return render(request, 'core/index.html', context)


@login_required
def company_detail_view(request, company_id):
    """Vista detallada de una empresa"""
    company = get_object_or_404(Company, id=company_id, is_active=True)
    
    # Verificar acceso del usuario
    user_can_access = False
    user_has_contributed = False
    user_review_status = None
    user_has_pending_review = False
    user_can_create_review = False
    
    if request.user.profile.role == 'company_rep':
        user_can_access = True
        user_can_create_review = False  # Los company_rep no pueden crear reseñas
    elif request.user.profile.role == 'candidate':
        # Verificar si tiene reseñas pendientes
        any_pending_reviews = PendingReview.objects.filter(
            user_profile=request.user.profile,
            is_reviewed=False
        ).exists()
        
        if any_pending_reviews:
            user_can_access = False
            user_has_pending_review = True
        else:
            user_can_access = True
            user_can_create_review = True  # Los candidatos pueden crear reseñas
            
            # Verificar reseñas para esta empresa
            user_reviews = Review.objects.filter(
                user_profile=request.user.profile,
                company=company
            )
            
            if user_reviews.exists():
                user_has_contributed = True
                latest_review = user_reviews.latest('submission_date')
                user_review_status = latest_review.status
    
    # Obtener reseñas
    approved_reviews = Review.objects.filter(
        company=company,
        status='approved'
    ).select_related('user_profile__user')
    
    pending_reviews = Review.objects.filter(
        company=company,
        status='pending'
    ).select_related('user_profile__user')
    
    rejected_reviews = Review.objects.filter(
        company=company,
        status='rejected'
    ).select_related('user_profile__user')
    
    # Combinar según rol
    if request.user.profile.role == 'company_rep' or request.user.is_staff:
        all_visible_reviews = list(approved_reviews) + list(pending_reviews) + list(rejected_reviews)
    else:
        all_visible_reviews = list(approved_reviews) + list(pending_reviews)
    
    # Reseña pendiente específica
    pending_review = None
    if request.user.profile.role == 'candidate':
        pending_review = PendingReview.objects.filter(
            user_profile=request.user.profile,
            company=company,
            is_reviewed=False
        ).first()
    
    # ===== Estadísticas y datos para gráficos =====
    # Para reputación base, por defecto usamos reseñas aprobadas.
    # Para candidatos, incluimos también 'pending' para evitar vacíos visuales
    # (el template ya controla acceso y no muestra a quienes tienen pendientes propias).
    if hasattr(request.user, 'profile') and request.user.profile.role == 'candidate':
        reviews_for_stats = Review.objects.filter(company=company, status__in=['approved', 'pending'])
    elif request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.role == 'company_rep'):
        reviews_for_stats = Review.objects.filter(company=company)
    else:
        reviews_for_stats = approved_reviews

    # Promedios numéricos
    from django.db.models import Avg as DJAvg, Count as DJCount

    avg_overall = reviews_for_stats.aggregate(v=DJAvg('overall_rating'))['v'] or 0

    # Mapear categorías a valores para promediar
    COMM_SCORES = {
        'excellent': 5,
        'good': 4,
        'regular': 3,
        'poor': 2,
    }
    DIFF_SCORES = {
        'very_easy': 1,
        'easy': 2,
        'moderate': 3,
        'difficult': 4,
        'very_difficult': 5,
    }
    RESP_SCORES = {
        'immediate': 5,
        'same_day': 4,
        'next_day': 3,
        'few_days': 2,
        'slow': 1,
    }

    def avg_from_choices(qs, field, scores):
        total = 0
        count = 0
        for val, c in qs.values_list(field).annotate(cnt=DJCount('pk')):
            if val in scores:
                total += scores[val] * qs.filter(**{field: val}).count()
                count += qs.filter(**{field: val}).count()
        return (total / count) if count else 0

    avg_communication = avg_from_choices(reviews_for_stats, 'communication_rating', COMM_SCORES)
    avg_difficulty = avg_from_choices(reviews_for_stats, 'difficulty_rating', DIFF_SCORES)
    avg_response_time = avg_from_choices(reviews_for_stats, 'response_time_rating', RESP_SCORES)

    total_reviews_stats = reviews_for_stats.count()
    company_stats = {
        'avg_overall': avg_overall,
        'avg_communication': avg_communication,
        'avg_difficulty': avg_difficulty,
        'avg_response_time': avg_response_time,
        'total_reviews': total_reviews_stats,
    }

    # Distribución de calificaciones (1-5)
    rating_counts = [
        reviews_for_stats.filter(overall_rating=i).count() for i in range(1, 6)
    ]

    # Distribución por modalidad
    MOD_LABELS = [('presencial', 'Presencial'), ('remoto', 'Remoto'), ('híbrido', 'Híbrido')]
    modality_counts = [reviews_for_stats.filter(modality=key).count() for key, _ in MOD_LABELS]

    # Estado (sobre todas las reseñas de la empresa para el representante)
    status_counts = [
        approved_reviews.count(),
        pending_reviews.count(),
        rejected_reviews.count(),
    ]

    # Timeline por mes (últimos 12 meses si aplica)
    monthly = (
        reviews_for_stats.annotate(m=TruncMonth('submission_date'))
        .values('m')
        .annotate(c=DJCount('id'))
        .order_by('m')
    )
    timeline_labels = [
        (item['m'].strftime('%b %Y') if item['m'] else '') for item in monthly
    ]
    timeline_counts = [item['c'] for item in monthly]

    # ===== Gráficos removidos - ya no se usan =====

    # Datos para gráficos (se generarán con Chart.js en el frontend)
    chart_data = {
        'ratings': [],
        'modality': [],
        'status': [],
        'timeline': []
    }
    
    if reviews_for_stats.exists():
        # Datos de distribución de calificaciones
        rating_counts = {}
        for i in range(1, 6):
            count = reviews_for_stats.filter(overall_rating=i).count()
            rating_counts[f'{i} estrella{"s" if i > 1 else ""}'] = count
        chart_data['ratings'] = rating_counts
        
        # Datos de modalidad
        modality_counts = {}
        for modality, _ in Review.MODALITY_CHOICES:
            count = reviews_for_stats.filter(modality=modality).count()
            if count > 0:
                modality_counts[modality.title()] = count
        chart_data['modality'] = modality_counts
        
        # Datos de estado
        status_counts = {}
        for status, _ in Review.STATUS_CHOICES:
            count = reviews_for_stats.filter(status=status).count()
            if count > 0:
                status_counts[status.title()] = count
        chart_data['status'] = status_counts
        
        # Datos de timeline (últimos 6 meses)
        timeline_data = {}
        for i in range(6):
            month_start = timezone.now() - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            count = reviews_for_stats.filter(
                submission_date__gte=month_start,
                submission_date__lt=month_end
            ).count()
            month_name = month_start.strftime('%b %Y')
            timeline_data[month_name] = count
        chart_data['timeline'] = timeline_data

    # ===== Estadísticas específicas por rol =====
    role_kpis = {}
    try:
        user_role = request.user.profile.role
    except Exception:
        user_role = None

    if user_role == 'candidate':
        # Estadísticas útiles para candidatos
        since_90 = timezone.now() - timedelta(days=90)
        last90_reviews = reviews_for_stats.filter(submission_date__gte=since_90)

        # Tasa de respuesta rápida (últimos 90 días)
        fast_responses = last90_reviews.filter(response_time_rating__in=['immediate', 'same_day']).count()
        fast_response_rate = (fast_responses / last90_reviews.count()) * 100 if last90_reviews.count() > 0 else 0

        # Modalidad más recomendada
        top_modality = reviews_for_stats.values('modality').annotate(
            count=DJCount('id'),
            avg_rating=Avg('overall_rating')
        ).order_by('-avg_rating', '-count').first()

        # Nivel de dificultad promedio
        difficulty_distribution = reviews_for_stats.values('difficulty_rating').annotate(
            count=DJCount('id')
        ).order_by('difficulty_rating')

        # Calidad de comunicación
        comm_distribution = reviews_for_stats.values('communication_rating').annotate(
            count=DJCount('id')
        ).order_by('communication_rating')

        role_kpis = {
            'role': 'candidate',
            'avg_overall': avg_overall,
            'last90_reviews_count': last90_reviews.count(),
            'fast_response_rate': round(fast_response_rate, 1),
            'top_modality': top_modality['modality'] if top_modality else None,
            'top_modality_rating': round(top_modality['avg_rating'], 1) if top_modality else 0,
            'difficulty_distribution': list(difficulty_distribution),
            'communication_distribution': list(comm_distribution),
            'total_reviews': reviews_for_stats.count(),
        }
    elif user_role == 'company_rep':
        # Estadísticas útiles para representantes de empresa
        all_company_reviews = Review.objects.filter(company=company)

        # Ratios de aprobación
        total_reviews = all_company_reviews.count()
        approved_count = all_company_reviews.filter(status='approved').count()
        pending_count = all_company_reviews.filter(status='pending').count()
        rejected_count = all_company_reviews.filter(status='rejected').count()

        approval_rate = (approved_count / total_reviews) * 100 if total_reviews > 0 else 0
        rejection_rate = (rejected_count / total_reviews) * 100 if total_reviews > 0 else 0

        # Compromiso de tiempo de respuesta (aprobadas con respuesta rápida)
        compromiso_compliant = all_company_reviews.filter(
            status='approved',
            response_time_rating__in=['immediate', 'same_day']
        ).count()
        compromiso_rate = (compromiso_compliant / approved_count) * 100 if approved_count > 0 else 0

        # Tendencia mensual (últimos 6 meses)
        six_months_ago = timezone.now() - timedelta(days=180)
        monthly_trend = all_company_reviews.filter(submission_date__gte=six_months_ago).annotate(
            month=TruncMonth('submission_date')
        ).values('month').annotate(
            count=DJCount('id'),
            approved=DJCount('id', filter=Q(status='approved')),
            avg_rating=Avg('overall_rating')
        ).order_by('month')

        # Calificaciones por mes
        monthly_ratings = list(monthly_trend)

        role_kpis = {
            'role': 'company_rep',
            'avg_overall': avg_overall,
            'total_reviews': total_reviews,
            'approved_count': approved_count,
            'pending_count': pending_count,
            'rejected_count': rejected_count,
            'approval_rate': round(approval_rate, 1),
            'rejection_rate': round(rejection_rate, 1),
            'compromiso_rate': round(compromiso_rate, 1),
            'monthly_trend': monthly_ratings,
            'avg_communication': avg_communication,
            'avg_difficulty': avg_difficulty,
            'avg_response_time': avg_response_time,
        }

    context = {
        'company': company,
        'approved_reviews': approved_reviews,
        'pending_reviews': pending_reviews,
        'rejected_reviews': rejected_reviews,
        'all_visible_reviews': all_visible_reviews,
        'user_can_access': user_can_access,
        'user_has_contributed': user_has_contributed,
        'user_review_status': user_review_status,
        'user_has_pending_review': user_has_pending_review,
        'user_can_create_review': user_can_create_review,
        'pending_review': pending_review,
        'company_stats': company_stats,
        'chart_data': chart_data,
        'role_kpis': role_kpis,
    }
    
    return render(request, 'core/company_detail.html', context)

# ===== VISTAS DE RESEÑAS =====

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

# ===== VISTAS DE PERFIL =====

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
        # Establecer queryset para empresas activas
        form.fields['company'].queryset = Company.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'title': 'Agregar Experiencia Laboral'
    }
    
    return render(request, 'core/add_work_history.html', context)

@login_required
def my_profile_view(request):
    """Vista para mostrar el perfil del usuario"""
    user_profile = request.user.profile
    
    if user_profile.role == 'candidate':
        # Estadísticas para candidatos
        total_reviews = Review.objects.filter(user_profile=user_profile).count()
        approved_reviews = Review.objects.filter(
            user_profile=user_profile,
            status='approved'
        ).count()
        pending_approval = Review.objects.filter(
            user_profile=user_profile,
            status='pending'
        ).count()
        
        pending_reviews = PendingReview.objects.filter(
            user_profile=user_profile,
            is_reviewed=False
        ).select_related('company')
        
        # Historial laboral
        work_history = WorkHistory.objects.filter(
            user_profile=user_profile
        ).select_related('company').order_by('-start_date')[:3]  # Solo las 3 más recientes para el perfil
        
        # Contar logros obtenidos
        achievement_count = UserAchievement.objects.filter(user_profile=user_profile).count()
        
        context = {
            'user_profile': user_profile,
            'total_reviews': total_reviews,
            'approved_reviews': approved_reviews,
            'pending_approval': pending_approval,
            'pending_reviews': pending_reviews,
            'work_history': work_history,
            'achievement_count': achievement_count,
            'show_stats': True,
        }
    else:
        context = {
            'user_profile': user_profile,
            'show_stats': False,
        }
    
    return render(request, 'core/profile.html', context)

# ===== VISTA DE LOGROS =====
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

# ===== ACTUALIZACIÓN DE PERFIL =====
@login_required
def update_profile_view(request):
    """Permite al usuario actualizar su nombre visible y foto."""
    user = request.user
    initial = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'display_name': getattr(user.profile, 'display_name', '')
    }

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ ¡Perfil actualizado correctamente! Los cambios se han guardado exitosamente.')
            return redirect('my_profile')
        else:
            # Mensajes de error específicos para perfil
            error_messages = {
                'first_name': 'El nombre debe tener entre 1 y 30 caracteres.',
                'last_name': 'El apellido debe tener entre 1 y 30 caracteres.',
                'display_name': 'El nombre visible debe tener máximo 100 caracteres.',
                'avatar': 'La imagen debe ser válida (JPG, PNG). Tamaño máximo recomendado: 2MB.'
            }
            
            for field, errors in form.errors.items():
                field_name = error_messages.get(field, field.replace('_', ' ').title())
                for error in errors:
                    messages.error(request, f'❌ {field_name}: {error}')
    else:
        form = ProfileUpdateForm(initial=initial, user=user)

    return render(request, 'core/profile_update.html', {'form': form})

# ===== VISTAS DE EMPRESA =====

@login_required
def company_dashboard_view(request):
    """Dashboard para representantes de empresa"""
    if request.user.profile.role != 'company_rep':
        messages.error(request, 'Acceso no autorizado.')
        return redirect('login')
    
    # Búsqueda
    search_query = request.GET.get('search', '')
    companies = Company.objects.filter(is_active=True).prefetch_related('reviews').order_by('name')
    
    if search_query:
        companies = companies.filter(
            Q(name__icontains=search_query) |
            Q(sector__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Estadísticas
    total_companies = companies.count()
    total_reviews = Review.objects.count()
    total_candidates = UserProfile.objects.filter(role='candidate').count()
    
    # Agregar info a cada empresa
    for company in companies:
        company_reviews = company.reviews.all()
        company.total_reviews = company_reviews.count()
        
        company_rated_reviews = company_reviews.filter(overall_rating__isnull=False)
        if company_rated_reviews.exists():
            company.avg_rating = company_rated_reviews.aggregate(avg=Avg('overall_rating'))['avg']
        else:
            company.avg_rating = 0
    
    context = {
        'companies': companies,
        'total_companies': total_companies,
        'total_reviews': total_reviews,
        'total_candidates': total_candidates,
        'search_query': search_query,
    }
    
    return render(request, 'core/company_dashboard.html', context)

# ===== VISTAS DEL STAFF =====
# (Eliminadas - ahora se usa moderación automática con machine learning)

def staff_dashboard_view(request):
    """Vista eliminada - redirige al dashboard principal"""
    messages.info(request, 'El panel de staff ha sido eliminado. Ahora se usa moderación automática.')
    return redirect('dashboard')


def create_user_view(request):
    """Vista eliminada - redirige al dashboard principal"""
    messages.info(request, 'La creación de usuarios por staff ha sido eliminada.')
    return redirect('dashboard')


def assign_company_view(request):
    """Vista para asignar empresas a usuarios"""
    if request.method == 'POST':
        # Manejar usuario preseleccionado
        user_id = request.GET.get('user')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                if hasattr(user, 'profile') and user.profile.role == 'candidate':
                    form_data = request.POST.copy()
                    form_data['user_profile'] = user.profile.id
                    form = StaffAssignmentForm(form_data)
                    form.fields['user_profile'].queryset = UserProfile.objects.filter(role='candidate').select_related('user')
                    form.fields['company'].queryset = Company.objects.filter(is_active=True)
                else:
                    form = StaffAssignmentForm(request.POST)
                    form.fields['user_profile'].queryset = UserProfile.objects.filter(role='candidate').select_related('user')
                    form.fields['company'].queryset = Company.objects.filter(is_active=True)
            except User.DoesNotExist:
                form = StaffAssignmentForm(request.POST)
                form.fields['user_profile'].queryset = UserProfile.objects.filter(role='candidate').select_related('user')
                form.fields['company'].queryset = Company.objects.filter(is_active=True)
        else:
            form = StaffAssignmentForm(request.POST)
            form.fields['user_profile'].queryset = UserProfile.objects.filter(role='candidate').select_related('user')
            form.fields['company'].queryset = Company.objects.filter(is_active=True)
        
        if form.is_valid():
            try:
                # Guardar asignación
                assignment = form.save(commit=False)
                assignment.staff_user = request.user
                assignment.save()
                
                # Crear reseña pendiente
                assignment.create_pending_review()
                
                # Actualizar onboarding
                onboarding_status, created = OnboardingStatus.objects.get_or_create(
                    user_profile=assignment.user_profile,
                    defaults={
                        'has_participated_in_selection': True,
                        'onboarding_completed': True,
                        'last_onboarding_date': timezone.now(),
                    },
                )
                onboarding_status.detect_participation_status()
                
                messages.success(request, f'✅ Empresa {assignment.company.name} asignada exitosamente a {assignment.user_profile.user.username}. Se ha creado una reseña pendiente.')
                return redirect('staff_dashboard')
            except Exception as e:
                messages.error(request, f'❌ Error al asignar empresa: {str(e)}. Verifica que todos los datos sean correctos e intenta nuevamente.')
        else:
            # Mensajes de error específicos para asignación
            error_messages = {
                'user_profile': 'Debes seleccionar un usuario candidato válido.',
                'company': 'Debes seleccionar una empresa activa.',
                'job_title': 'El cargo es obligatorio. Ejemplo: "Desarrollador Backend", "Diseñador UX".',
                'participation_date': 'La fecha de participación es obligatoria y debe ser válida.'
            }
            
            for field, errors in form.errors.items():
                field_name = error_messages.get(field, field.replace('_', ' ').title())
                for error in errors:
                    messages.error(request, f'❌ {field_name}: {error}')
    else:
        form = StaffAssignmentForm()
        # Establecer querysets requeridos para evitar None en prefetch
        form.fields['user_profile'].queryset = UserProfile.objects.filter(role='candidate').select_related('user')
        form.fields['company'].queryset = Company.objects.filter(is_active=True)
        
        # Preseleccionar usuario
        user_id = request.GET.get('user')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                if hasattr(user, 'profile') and user.profile.role == 'candidate':
                    form.initial['user_profile'] = user.profile
            except User.DoesNotExist:
                pass
    
    context = {
        'form': form,
        'title': 'Asignar Empresa a Usuario'
    }
    
    return render(request, 'core/staff_assign_company.html', context)


def delete_review_view(request, review_id):
    """Vista eliminada - redirige al dashboard principal"""
    messages.info(request, 'La eliminación manual de reseñas ha sido eliminada. Ahora se usa moderación automática.')
    return redirect('dashboard')


def approve_review_view(request, review_id):
    """Vista eliminada - redirige al dashboard principal"""
    messages.info(request, 'La moderación manual de reseñas ha sido eliminada. Ahora se usa moderación automática con machine learning.')
    return redirect('dashboard')


@login_required
def export_company_reviews_csv(request, company_id):
    """Exporta reseñas de una empresa en CSV. company_rep/staff únicamente."""
    company = get_object_or_404(Company, id=company_id, is_active=True)

    # Permisos: staff o company_rep
    if not (request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.role == 'company_rep')):
        messages.error(request, 'Acceso no autorizado.')
        return redirect('login')

    qs = Review.objects.filter(company=company).select_related('user_profile__user').order_by('-submission_date')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{company.name}_reviews.csv"'

    # Escribir CSV manualmente (sin depender de csv para controlar UTF-8 con BOM)
    response.write('\ufeff')  # BOM para Excel
    headers = [
        'username', 'job_title', 'modality', 'communication_rating', 'difficulty_rating',
        'response_time_rating', 'overall_rating', 'status', 'submission_date'
    ]
    response.write(','.join(headers) + '\n')

    def esc(val):
        if val is None:
            return ''
        s = str(val).replace('"', '""')
        if ',' in s or '"' in s or '\n' in s:
            s = '"' + s + '"'
        return s

    for r in qs:
        row = [
            r.user_profile.user.username,
            r.job_title,
            r.modality,
            r.communication_rating,
            r.difficulty_rating,
            r.response_time_rating,
            r.overall_rating,
            r.status,
            r.submission_date.strftime('%Y-%m-%d %H:%M'),
        ]
        response.write(','.join(esc(v) for v in row) + '\n')

    return response

# =============================================================================
# VISTAS SEO - Optimización para Motores de Búsqueda
# =============================================================================

def robots_txt_view(request):
    """
    Vista para servir el archivo robots.txt - Guía para motores de búsqueda

    Genera dinámicamente el archivo robots.txt que indica a los motores de búsqueda:
    - Qué páginas pueden indexar
    - Qué páginas deben evitar
    - Ubicación del sitemap.xml

    SEO Benefits:
    - Controla qué contenido indexan los motores de búsqueda
    - Evita indexación de áreas sensibles (admin, staff)
    - Referencia al sitemap para mejor crawling
    """
    from django.template.loader import render_to_string

    # Obtener el protocolo y dominio para URLs absolutas
    protocol = 'https' if request.is_secure() else 'http'
    domain = request.get_host()

    context = {
        'protocol': protocol,
        'domain': domain,
    }

    robots_content = render_to_string('core/robots.txt', context)
    return HttpResponse(robots_content, content_type='text/plain')


def sitemap_xml_view(request):
    """
    Vista para servir el archivo sitemap.xml - Mapa del sitio para SEO

    Genera dinámicamente el sitemap XML que incluye:
    - Página principal y páginas estáticas
    - Todas las empresas activas con sus URLs
    - Metadatos de última modificación y prioridad

    SEO Benefits:
    - Ayuda a motores de búsqueda a encontrar todas las páginas
    - Proporciona información sobre frecuencia de actualización
    - Prioriza páginas importantes para crawling
    - Incluye datos geo-localizados para SEO local
    """
    from django.template.loader import render_to_string

    # Obtener todas las empresas activas para incluir en sitemap
    companies = Company.objects.filter(is_active=True).order_by('name')

    # Obtener el protocolo y dominio para URLs absolutas
    protocol = 'https' if request.is_secure() else 'http'
    domain = request.get_host()

    context = {
        'companies': companies,
        'protocol': protocol,
        'domain': domain,
    }

    sitemap_content = render_to_string('core/sitemap.xml', context)
    return HttpResponse(sitemap_content, content_type='application/xml')