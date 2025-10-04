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
from companies.models import Company
from accounts.models import UserProfile, OnboardingStatus
from reviews.models import Review, PendingReview
from work_history.models import WorkHistory
from achievements.models import Achievement, UserAchievement
# Los formularios han sido movidos a sus respectivas aplicaciones
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
        
        # Satisfacción por sector (gráfico nuevo)
        sector_satisfaction = {}
        from django.db.models import Avg, Count
        sector_ratings = user_reviews.values('company__sector').annotate(
            avg_rating=Avg('overall_rating'),
            count=Count('id')
        ).filter(count__gte=1)  # Solo sectores con al menos 1 reseña
        
        for item in sector_ratings:
            sector_name = item['company__sector'] or 'Sin especificar'
            sector_satisfaction[sector_name] = round(item['avg_rating'], 1)
        context['chart_data']['sector_satisfaction'] = sector_satisfaction
    
    return render(request, 'core/index.html', context)


# ===== VISTA MOVIDA A COMPANIES/VIEWS.PY =====
# La función company_detail_view ha sido movida a companies/views.py
# para mejor modularización del proyecto

# ===== VISTAS DE RESEÑAS =====

# ===== VISTAS MOVIDAS A REVIEWS/VIEWS.PY =====
# Las funciones create_review_view y my_reviews_view han sido movidas a reviews/views.py
# para mejor modularización del proyecto

# ===== VISTAS DE PERFIL =====

# ===== VISTAS MOVIDAS A WORK_HISTORY/VIEWS.PY =====
# Las funciones work_history_view y add_work_history_view han sido movidas a work_history/views.py
# para mejor modularización del proyecto

# ===== VISTA MOVIDA A ACCOUNTS/VIEWS.PY =====
# La función my_profile_view ha sido movida a accounts/views.py
# para mejor modularización del proyecto

# ===== VISTA MOVIDA A ACHIEVEMENTS/VIEWS.PY =====
# La función achievements_view ha sido movida a achievements/views.py
# para mejor modularización del proyecto

# ===== VISTA MOVIDA A ACCOUNTS/VIEWS.PY =====
# La función update_profile_view ha sido movida a accounts/views.py
# para mejor modularización del proyecto

# ===== VISTA MOVIDA A COMPANIES/VIEWS.PY =====
# La función company_dashboard_view ha sido movida a companies/views.py
# para mejor modularización del proyecto
# Función eliminada - movida a companies/views.py
    
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
    
    # ===== DATOS PARA GRÁFICOS DEL DASHBOARD =====
    chart_data = {
        'sector_distribution': {},
        'location_distribution': {},
        'rating_distribution': {},
        'monthly_trend': {},
        'top_companies': {},
        'review_status': {}
    }
    
    # Distribución por sector
    sector_stats = companies.values('sector').annotate(
        count=Count('id'),
        avg_rating=Avg('reviews__overall_rating'),
        total_reviews=Count('reviews')
    ).order_by('-count')
    
    for stat in sector_stats:
        sector_name = stat['sector'] or 'Sin especificar'
        chart_data['sector_distribution'][sector_name] = {
            'companies': stat['count'],
            'avg_rating': round(stat['avg_rating'] or 0, 1),
            'total_reviews': stat['total_reviews']
        }
    
    # Distribución por ubicación
    location_stats = companies.values('location').annotate(
        count=Count('id'),
        avg_rating=Avg('reviews__overall_rating')
    ).order_by('-count')[:10]  # Top 10 ciudades
    
    for stat in location_stats:
        location_name = stat['location'] or 'Sin especificar'
        chart_data['location_distribution'][location_name] = {
            'companies': stat['count'],
            'avg_rating': round(stat['avg_rating'] or 0, 1)
        }
    
    # Distribución de calificaciones generales
    all_reviews = Review.objects.all()
    if all_reviews.exists():
        for i in range(1, 6):
            count = all_reviews.filter(overall_rating=i).count()
            chart_data['rating_distribution'][f'{i} estrella{"s" if i > 1 else ""}'] = count
    
    # Tendencia mensual de reseñas (últimos 6 meses)
    for i in range(6):
        month_start = timezone.now() - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        count = all_reviews.filter(
            submission_date__gte=month_start,
            submission_date__lt=month_end
        ).count()
        month_name = month_start.strftime('%b %Y')
        chart_data['monthly_trend'][month_name] = count
    
    # Top empresas por calificación
    top_companies = companies.annotate(
        avg_rating=Avg('reviews__overall_rating'),
        review_count=Count('reviews')
    ).filter(
        review_count__gte=1
    ).order_by('-avg_rating', '-review_count')[:10]
    
    for company in top_companies:
        if company.avg_rating:
            chart_data['top_companies'][company.name] = {
                'rating': round(company.avg_rating, 1),
                'reviews': company.review_count
            }
    
    # Estado de reseñas
    approved_count = all_reviews.filter(status='approved').count()
    pending_count = all_reviews.filter(status='pending').count()
    rejected_count = all_reviews.filter(status='rejected').count()
    
    chart_data['review_status'] = {
        'Aprobadas': approved_count,
        'Pendientes': pending_count,
        'Rechazadas': rejected_count
    }
    
    context = {
        'companies': companies,
        'total_companies': total_companies,
        'total_reviews': total_reviews,
        'total_candidates': total_candidates,
        'search_query': search_query,
        'chart_data': chart_data,
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
    """Vista eliminada - redirige al dashboard principal"""
    messages.info(request, 'La asignación manual de empresas ha sido eliminada. Ahora se usa el sistema de historial laboral automático.')
    return redirect('dashboard')


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

def robots_txt_view(request):
    """Vista para robots.txt"""
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    
    content = render_to_string('core/robots.txt', {
        'request': request
    })
    return HttpResponse(content, content_type='text/plain')

