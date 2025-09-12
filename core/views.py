# ===== VISTAS DE LA APLICACIÓN CORE =====
# Maneja las peticiones HTTP y renderiza templates

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Company, UserProfile, Review, OnboardingStatus, PendingReview, StaffAssignment
from .forms import ReviewForm, UserCreationForm, StaffAssignmentForm, ProfileUpdateForm
from django.db.models.functions import TruncMonth
import json
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.http import HttpResponse
from datetime import timedelta

# ===== FUNCIONES AUXILIARES =====

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
    """Dashboard principal para candidatos"""
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
            Q(location__icontains=search_query)
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
    }
    
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
    
    if request.user.profile.role == 'company_rep':
        user_can_access = True
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

    # ===== Render de gráficos en Python (matplotlib) - robusto y desde cero =====
    def fig_to_datauri(fig):
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format='png', dpi=140)
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        return f"data:image/png;base64,{b64}"

    def make_bar(labels, counts, title, xlabel, ylabel):
        fig, ax = plt.subplots(figsize=(4.5, 2.6))
        x = list(range(len(labels)))
        ax.bar(x, counts, color='#1E3A8A')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=8)
        ax.set_ylim(bottom=0)
        return fig_to_datauri(fig)

    def make_pie(labels, counts, title):
        total = sum(counts)
        fig, ax = plt.subplots(figsize=(4.2, 2.6))
        if total > 0:
            ax.pie(counts, labels=labels, autopct='%1.0f%%', textprops={'fontsize': 8})
        else:
            ax.text(0.5, 0.5, 'Sin datos', ha='center', va='center')
            ax.axis('off')
        ax.set_title(title)
        return fig_to_datauri(fig)

    def make_line(labels, counts, title):
        fig, ax = plt.subplots(figsize=(6.0, 2.6))
        if counts:
            x = list(range(len(labels)))
            ax.plot(x, counts, marker='o', color='#1E3A8A')
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7)
        else:
            ax.text(0.5, 0.5, 'Sin datos', ha='center', va='center')
            ax.axis('off')
        ax.set_title(title)
        ax.set_ylabel('Cantidad')
        return fig_to_datauri(fig)

    ratings_img = make_bar(['1', '2', '3', '4', '5'], rating_counts, 'Distribución de Calificaciones', 'Calificación', 'Cantidad')
    modality_img = make_pie([lbl for _, lbl in MOD_LABELS], modality_counts, 'Modalidad de Reseñas')
    status_img = make_pie(['Aprobadas', 'Pendientes', 'Rechazadas'], status_counts, 'Estado de Reseñas')
    timeline_img = make_line(timeline_labels, timeline_counts, 'Reseñas por Mes')

    # ===== Resúmenes por rol =====
    role_kpis = {}
    try:
        user_role = request.user.profile.role
    except Exception:
        user_role = None

    if user_role == 'candidate':
        # Últimos 90 días
        from django.utils import timezone
        since_90 = timezone.now() - timedelta(days=90)
        last90 = reviews_for_stats.filter(submission_date__gte=since_90)
        last90_count = last90.count()
        fast_count = last90.filter(response_time_rating__in=['immediate', 'same_day']).count()
        fast_rate = (fast_count / last90_count) if last90_count else 0
        # Modalidad más común
        top_mod = (
            reviews_for_stats.values('modality')
            .annotate(c=DJCount('id')).order_by('-c').first()
        )
        role_kpis = {
            'role': 'candidate',
            'avg_overall': avg_overall,
            'last90_reviews': last90_count,
            'fast_response_rate': fast_rate,
            'top_modality': top_mod['modality'] if top_mod else None,
        }
    elif user_role == 'company_rep':
        total_all = approved_reviews.count() + pending_reviews.count() + rejected_reviews.count()
        sla_fast = approved_reviews.filter(response_time_rating__in=['immediate', 'same_day']).count()
        sla_rate = (sla_fast / approved_reviews.count()) if approved_reviews.count() else 0
        # Delta mensual (último vs anterior)
        last_two = (
            reviews_for_stats.annotate(m=TruncMonth('submission_date'))
            .values('m').annotate(c=DJCount('id')).order_by('-m')[:2]
        )
        month_delta = 0
        if len(last_two) == 2:
            month_delta = (last_two[0]['c'] - last_two[1]['c'])
        role_kpis = {
            'role': 'company_rep',
            'avg_overall': avg_overall,
            'sla_fast_rate': sla_rate,
            'approval_ratio': (approved_reviews.count() / total_all) if total_all else 0,
            'month_delta': month_delta,
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
        'pending_review': pending_review,
        'company_stats': company_stats,
        'ratings_img': ratings_img or '',
        'modality_img': modality_img or '',
        'status_img': status_img or '',
        'timeline_img': timeline_img or '',
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
    
    # Obtener empresas con reseñas pendientes
    pending_companies = PendingReview.objects.filter(
        user_profile=request.user.profile,
        is_reviewed=False
    ).select_related('company')
    
    if not pending_companies.exists():
        messages.warning(request, '⚠️ No tienes reseñas pendientes para crear. Contacta al staff para que te asignen una empresa.')
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
                
                # Marcar pendiente como completada
                company = form.cleaned_data['company']
                pending_review = PendingReview.objects.filter(
                    user_profile=request.user.profile,
                    company=company,
                    is_reviewed=False
                ).first()
                
                if pending_review:
                    pending_review.is_reviewed = True
                    pending_review.save()
                
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
                
                # Mensaje especial si era una reseña pendiente
                if pending_review:
                    messages.success(request, f'🎉 ¡Reseña completada exitosamente! Has completado tu reseña para {company.name}. Ahora puedes acceder a todas las empresas del sistema.')
                else:
                    messages.success(request, '¡Reseña enviada exitosamente! 🎉 Tu reseña está pendiente de aprobación y será revisada por nuestro equipo.')
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
                initial_data['company'] = company
            except Company.DoesNotExist:
                pass
        
        form = ReviewForm(initial=initial_data)
        form.fields['company'].queryset = Company.objects.filter(
            pending_reviews__user_profile=request.user.profile,
            pending_reviews__is_reviewed=False
        )
    
    context = {
        'form': form,
        'pending_companies': pending_companies,
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
        
        context = {
            'user_profile': user_profile,
            'total_reviews': total_reviews,
            'approved_reviews': approved_reviews,
            'pending_approval': pending_approval,
            'pending_reviews': pending_reviews,
            'show_stats': True,
        }
    else:
        context = {
            'user_profile': user_profile,
            'show_stats': False,
        }
    
    return render(request, 'core/profile.html', context)


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

@login_required
@user_passes_test(is_staff_user)
def staff_dashboard_view(request):
    """Dashboard para el staff del sistema"""
    # Búsqueda
    search_query = request.GET.get('search', '')
    
    # Obtener candidatos
    candidates = UserProfile.objects.filter(role='candidate').annotate(
        pending_reviews_count=Count('pending_reviews', filter=Q(pending_reviews__is_reviewed=False))
    ).prefetch_related(
        'pending_reviews__company'
    ).order_by('user__username')
    
    if search_query:
        candidates = candidates.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    # Convertir a lista
    candidates_list = []
    for candidate in candidates:
        pending_reviews = PendingReview.objects.filter(
            user_profile=candidate,
            is_reviewed=False
        ).select_related('company')
        
        candidate.pending_reviews_list = list(pending_reviews)
        candidates_list.append(candidate)
    
    # Obtener reseñas
    all_reviews = Review.objects.all().select_related(
        'user_profile__user', 'company'
    ).order_by('-submission_date')
    
    # Estadísticas
    total_candidates = len(candidates_list)
    candidates_with_pending = sum(1 for c in candidates_list if c.pending_reviews_count > 0)
    candidates_free = total_candidates - candidates_with_pending
    total_reviews = all_reviews.count()
    approved_reviews = all_reviews.filter(status='approved').count()
    pending_reviews = all_reviews.filter(status='pending').count()
    rejected_reviews = all_reviews.filter(status='rejected').count()
    
    context = {
        'candidates': candidates_list,
        'all_reviews': all_reviews,
        'total_candidates': total_candidates,
        'candidates_with_pending': candidates_with_pending,
        'candidates_free': candidates_free,
        'total_reviews': total_reviews,
        'approved_reviews': approved_reviews,
        'pending_reviews': pending_reviews,
        'rejected_reviews': rejected_reviews,
        'search_query': search_query,
    }
    
    return render(request, 'core/staff_dashboard.html', context)


@login_required
@user_passes_test(is_staff_user)
def create_user_view(request):
    """Vista para crear nuevos usuarios"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Crear perfil
            UserProfile.objects.create(
                user=user,
                role='candidate'
            )
            
            messages.success(request, f'✅ Usuario {user.username} creado exitosamente. Se ha asignado el rol de candidato por defecto.')
            return redirect('staff_dashboard')
    else:
        form = UserCreationForm()
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Usuario'
    }
    
    return render(request, 'core/staff_create_user.html', context)


@login_required
@user_passes_test(is_staff_user)
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


@login_required
@user_passes_test(is_staff_user)
def delete_review_view(request, review_id):
    """Vista para eliminar reseñas"""
    review = get_object_or_404(Review, id=review_id)
    
    if request.method == 'POST':
        company_name = review.company.name
        user_name = review.user_profile.user.username
        review.delete()
        messages.success(request, f'✅ Reseña de {user_name} para {company_name} eliminada exitosamente.')
        return redirect('staff_dashboard')
    
    context = {
        'review': review,
        'title': 'Confirmar Eliminación de Reseña'
    }
    
    return render(request, 'core/staff_delete_review.html', context)


@login_required
@user_passes_test(is_staff_user)
def approve_review_view(request, review_id):
    """Vista para aprobar o rechazar reseñas"""
    review = get_object_or_404(Review, id=review_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            review.status = 'approved'
            review.is_approved = True
            messages.success(request, f'✅ Reseña de {review.user_profile.user.username} para {review.company.name} aprobada exitosamente. Ya es visible para otros usuarios.')
        elif action == 'reject':
            review.status = 'rejected'
            review.is_approved = False
            messages.success(request, f'⚠️ Reseña de {review.user_profile.user.username} para {review.company.name} rechazada. No será visible para otros usuarios.')
        
        review.save()
        return redirect('staff_dashboard')
    
    context = {
        'review': review,
        'title': 'Gestionar Reseña'
    }
    
    return render(request, 'core/staff_manage_review.html', context)


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