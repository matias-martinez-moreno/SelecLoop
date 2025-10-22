# =============================================================================
# VISTAS DE LA APLICACIÓN CORE - SelecLoop
# =============================================================================
# Este archivo contiene las vistas principales del sistema SelecLoop
#
# Funcionalidades principales:
# - Dashboard principal para candidatos
# - Redirección inicial según rol
# - SEO: Sitemap y robots.txt dinámicos
# - Exportación de datos (CSV)
# =============================================================================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from companies.models import Company
from accounts.models import UserProfile
from reviews.models import Review, PendingReview
from work_history.models import WorkHistory
from achievements.models import Achievement, UserAchievement
from django.db.models.functions import TruncMonth
from datetime import timedelta


# ===== VISTAS PRINCIPALES =====

def root_redirect_view(request):
    """Redirección inicial según el estado de autenticación del usuario"""
    if request.user.is_authenticated:
        # Usuario autenticado - redirigir según rol
        try:
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
        except Exception:
            # Si hay algún error con el perfil, redirigir al dashboard
            return redirect('dashboard')
    else:
        # Usuario no autenticado - redirigir al login
        return redirect('login')


@login_required
def dashboard_view(request):
    """
    Dashboard principal para candidatos - Vista central de SelecLoop

    Esta vista muestra:
    - Lista de empresas disponibles para reseñar
    - Reseñas pendientes del usuario
    - Filtros por nombre, ciudad, sector y modalidad
    - Estado de acceso a cada empresa
    """
    # Obtener parámetros de filtro
    search_query = request.GET.get('search', '')
    city_filter = request.GET.get('city', '')
    sector_filter = request.GET.get('sector', '')
    modality_filter = request.GET.get('modality', '')
    
    # Base query para empresas activas
    companies = Company.objects.filter(is_active=True).prefetch_related('reviews').order_by('name')
    
    # Aplicar filtros
    if search_query:
        companies = companies.filter(
            Q(name__icontains=search_query) |
            Q(sector__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    if city_filter:
        companies = companies.filter(location__icontains=city_filter)
    
    if sector_filter:
        companies = companies.filter(sector__icontains=sector_filter)
    
    if modality_filter:
        companies = companies.filter(reviews__modality=modality_filter).distinct()
    
    # Obtener reseñas pendientes del usuario
    pending_reviews = PendingReview.objects.filter(
        user_profile=request.user.profile,
        is_reviewed=False
    ).select_related('company')
    
    # Obtener historial laboral con reseñas pendientes
    work_history_pending = WorkHistory.objects.filter(
        user_profile=request.user.profile,
        has_review_pending=True
    ).select_related('company')
    
    # Combinar ambas fuentes de reseñas pendientes, evitando duplicados
    all_pending_companies = []
    pending_company_ids = set()
    
    # Agregar reseñas pendientes
    for pending in pending_reviews:
        if pending.company.id not in pending_company_ids:
            all_pending_companies.append(pending)
            pending_company_ids.add(pending.company.id)
    
    # Agregar historial laboral pendiente (solo si no está ya en pending_reviews)
    for work in work_history_pending:
        if work.company.id not in pending_company_ids:
            all_pending_companies.append(work)
            pending_company_ids.add(work.company.id)
    
    # Agregar información adicional a cada empresa
    for company in companies:
        company_reviews = company.reviews.all()
        company.total_reviews = company_reviews.count()
        
        # Calcular calificación promedio
        company_rated_reviews = company_reviews.filter(overall_rating__isnull=False)
        if company_rated_reviews.exists():
            company.avg_rating = company_rated_reviews.aggregate(avg=Avg('overall_rating'))['avg']
        else:
            company.avg_rating = 0
    
        # Verificar si el usuario puede acceder a esta empresa
        user_can_access = True
        if pending_reviews.filter(company=company).exists():
            user_can_access = False
        
        company.user_can_access = user_can_access
    
    # Obtener valores únicos para filtros
    cities = Company.objects.filter(is_active=True).values_list('location', flat=True).distinct().order_by('location')
    sectors = Company.objects.filter(is_active=True).values_list('sector', flat=True).distinct().order_by('sector')
    
    # Datos para gráficos (si hay empresas)
    chart_data = {
        'sector_distribution': {},
        'location_distribution': {},
        'rating_distribution': {},
        'monthly_trend': {},
        'top_companies': {},
        'review_status': {}
    }
    
    if companies.exists():
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
        
        # Distribución de calificaciones
        rating_stats = Review.objects.values('overall_rating').annotate(
            count=Count('id')
        ).order_by('overall_rating')
        
        for stat in rating_stats:
            if stat['overall_rating'] is not None:
                rating_key = f"{stat['overall_rating']} estrella{'s' if stat['overall_rating'] > 1 else ''}"
                chart_data['rating_distribution'][rating_key] = stat['count']
        
        # Tendencia mensual (últimos 6 meses)
        six_months_ago = timezone.now() - timedelta(days=180)
        monthly_stats = Review.objects.filter(
            submission_date__gte=six_months_ago
        ).annotate(
            month=TruncMonth('submission_date')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        for stat in monthly_stats:
            if stat['month']:
                month_name = stat['month'].strftime('%b %Y')
                chart_data['monthly_trend'][month_name] = stat['count']
        
        # Top empresas por calificación
        top_companies_stats = companies.annotate(
            avg_rating=Avg('reviews__overall_rating'),
            review_count=Count('reviews')
        ).filter(
            avg_rating__isnull=False,
            review_count__gte=1
        ).order_by('-avg_rating', '-review_count')[:10]
        
        for company in top_companies_stats:
            chart_data['top_companies'][company.name] = {
                'avg_rating': round(company.avg_rating, 1),
                'review_count': company.review_count
            }
        
        # Estado de reseñas
        review_status_stats = Review.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        for stat in review_status_stats:
            status_name = dict(Review.STATUS_CHOICES).get(stat['status'], stat['status'])
            chart_data['review_status'][status_name] = stat['count']
        
        # Satisfacción por sector (para gráfico de satisfacción)
        sector_satisfaction = {}
        for stat in sector_stats:
            if stat['avg_rating'] is not None and stat['total_reviews'] > 0:
                sector_name = stat['sector'] or 'Sin especificar'
                sector_satisfaction[sector_name] = {
                    'avg_rating': round(stat['avg_rating'], 1),
                    'total_reviews': stat['total_reviews']
                }
        
        chart_data['sector_satisfaction'] = sector_satisfaction

    # Modalidades disponibles para el filtro
    modality_choices = [
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('híbrido', 'Híbrido'),
    ]

    context = {
        'companies': companies,
        'pending_reviews': all_pending_companies,
        'cities': cities,
        'sectors': sectors,
        'modality_choices': modality_choices,
        'search_query': search_query,
        'city_filter': city_filter,
        'sector_filter': sector_filter,
        'modality_filter': modality_filter,
        'chart_data': chart_data,
    }
    
    return render(request, 'core/index.html', context)


# ===== VISTAS SEO =====

def sitemap_xml_view(request):
    """
    Vista para servir el archivo sitemap.xml - Mapa del sitio para SEO
    """
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
    content = render_to_string('core/robots.txt', {
        'request': request
    })
    return HttpResponse(content, content_type='text/plain')


# ===== VISTAS DE EXPORTACIÓN =====

@login_required
def export_company_reviews_csv(request, company_id):
    """Exporta las reseñas de una empresa específica en formato CSV"""
    from django.http import HttpResponse
    import csv
    
    # Verificar permisos
    if not (request.user.is_staff or 
            (hasattr(request.user, 'profile') and request.user.profile.role == 'company_rep')):
        messages.error(request, 'Acceso no autorizado.')
        return redirect('dashboard')
    
    company = get_object_or_404(Company, id=company_id)
    reviews = Review.objects.filter(company=company).select_related('user_profile__user')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reseñas_{company.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Fecha', 'Usuario', 'Cargo', 'Modalidad', 'Calificación General',
        'Comunicación', 'Dificultad', 'Tiempo de Respuesta', 'Pros', 'Contras',
        'Preguntas de Entrevista', 'Estado'
    ])
    
    for review in reviews:
        writer.writerow([
            review.submission_date.strftime('%d/%m/%Y'),
            review.user_profile.user.username,
            review.job_title,
            review.get_modality_display(),
            review.overall_rating,
            review.get_communication_rating_display(),
            review.get_difficulty_rating_display(),
            review.get_response_time_rating_display(),
            review.pros,
            review.cons,
            review.interview_questions,
            review.get_status_display()
        ])
    
    return response
