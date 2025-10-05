# =============================================================================
# VISTAS DE LA APLICACIÓN COMPANIES - SelecLoop
# =============================================================================
# Este archivo contiene las vistas relacionadas con empresas
#
# Vistas principales:
# - company_detail_view: Vista detallada de una empresa
# - company_dashboard_view: Dashboard para representantes de empresa
# =============================================================================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.db.models.functions import TruncMonth
from .models import Company
from accounts.models import UserProfile
from .forms import CompanyEditForm


@login_required
def company_detail_view(request, company_id):
    """Vista detallada de una empresa"""
    company = get_object_or_404(Company, id=company_id, is_active=True)
    
    # Importar modelos necesarios
    from reviews.models import Review, PendingReview
    
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
    from django.utils import timezone
    from datetime import timedelta

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

    # ===== DATOS PARA GRÁFICOS =====
    chart_data = {
        'ratings': {},
        'modality': {},
        'status': {},
        'timeline': {},
        'strengths_weaknesses': {}
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
        
        # Datos de timeline (4 meses hacia atrás, ordenados de menor a mayor)
        timeline_data = {}
        from datetime import datetime
        import calendar
        
        current_date = timezone.now()
        
        # Crear lista de meses para ordenar después
        months_data = []
        
        for i in range(4):  # Cambiado a 4 meses
            # Calcular el mes correcto (hacia atrás desde el mes actual)
            target_month = current_date.month - i
            target_year = current_date.year
            
            # Si el mes es negativo o cero, ajustar al año anterior
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            
            # Primer día del mes
            month_start = timezone.make_aware(datetime(target_year, target_month, 1))
            
            # Último día del mes
            last_day = calendar.monthrange(target_year, target_month)[1]
            month_end = timezone.make_aware(datetime(target_year, target_month, last_day, 23, 59, 59))
            
            count = reviews_for_stats.filter(
                submission_date__gte=month_start,
                submission_date__lte=month_end
            ).count()
            
            month_name = month_start.strftime('%b %Y')
            months_data.append((month_start, month_name, count))
        
        # Ordenar de menor a mayor (más antiguo primero)
        months_data.sort(key=lambda x: x[0])
        
        # Crear diccionario ordenado
        for month_start, month_name, count in months_data:
            timeline_data[month_name] = count
        
        chart_data['timeline'] = timeline_data
        
        # Debug: Agregar información adicional para verificar
        chart_data['debug_info'] = {
            'total_reviews': reviews_for_stats.count(),
            'latest_review_date': reviews_for_stats.order_by('-submission_date').first().submission_date if reviews_for_stats.exists() else None,
            'current_time': timezone.now().isoformat(),
            'ratings_data': chart_data['ratings'],
            'modality_data': chart_data['modality'],
            'status_data': chart_data['status'],
            'timeline_data': chart_data['timeline'],
            'strengths_data': chart_data['strengths_weaknesses']
        }
        
        # Gráfico de Fortalezas y Debilidades (Radar Chart)
        strengths_weaknesses = {}
        from django.db.models import Avg
        
        # Calcular promedios por aspecto (usando solo campos disponibles)
        aspects = {
            'communication_rating': 'Comunicación',
            'difficulty_rating': 'Dificultad del Proceso', 
            'response_time_rating': 'Tiempo de Respuesta',
            'overall_rating': 'Calificación General'
        }
        
        for field, label in aspects.items():
            if field == 'overall_rating':
                # Para overall_rating usamos Avg directamente
                avg_rating = reviews_for_stats.aggregate(
                    avg=Avg(field)
                )['avg']
                if avg_rating is not None:
                    strengths_weaknesses[label] = round(avg_rating, 1)
            else:
                # Para los otros campos, necesitamos convertir las opciones a números
                # Mapeo de opciones a valores numéricos
                rating_mapping = {
                    'communication_rating': {
                        'excellent': 5, 'good': 4, 'regular': 3, 'poor': 2
                    },
                    'difficulty_rating': {
                        'very_easy': 1, 'easy': 2, 'moderate': 3, 'difficult': 4, 'very_difficult': 5
                    },
                    'response_time_rating': {
                        'immediate': 5, 'same_day': 4, 'next_day': 3, 'few_days': 2, 'slow': 1
                    }
                }
                
                # Calcular promedio manualmente
                total_score = 0
                count = 0
                for review in reviews_for_stats:
                    rating_value = rating_mapping[field].get(getattr(review, field), 0)
                    if rating_value > 0:
                        total_score += rating_value
                        count += 1
                
                if count > 0:
                    avg_rating = total_score / count
                    strengths_weaknesses[label] = round(avg_rating, 1)
        
        chart_data['strengths_weaknesses'] = strengths_weaknesses
    
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
            avg_rating=DJAvg('overall_rating')
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


@login_required
def company_dashboard_view(request):
    """Dashboard para representantes de empresa"""
    if request.user.profile.role != 'company_rep':
        messages.error(request, 'Acceso no autorizado.')
        return redirect('login')
    
    # Importar modelos necesarios
    from reviews.models import Review
    
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
            company.avg_rating = company_reviews.aggregate(avg=Avg('overall_rating'))['avg']
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


@login_required
def edit_company_view(request, company_id):
    """Vista para editar información de empresa (solo para company_rep)"""
    company = get_object_or_404(Company, id=company_id)
    
    # Verificar que el usuario es company_rep
    if request.user.profile.role != 'company_rep':
        messages.error(request, 'No tienes permisos para editar empresas.')
        return redirect('company_detail', company_id=company.id)
    
    if request.method == 'POST':
        form = CompanyEditForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Información de la empresa actualizada exitosamente.')
            return redirect('company_detail', company_id=company.id)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CompanyEditForm(instance=company)
    
    context = {
        'form': form,
        'company': company,
    }
    
    return render(request, 'companies/edit_company.html', context)