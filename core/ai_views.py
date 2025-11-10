# =============================================================================
# VISTAS AEO - AI Engine Optimization
# =============================================================================
# Este archivo contiene vistas específicas para optimizar el contenido
# para motores de inteligencia artificial (ChatGPT, Claude, Gemini, etc.)
# =============================================================================

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Avg, Count
from companies.models import Company
from reviews.models import Review
from accounts.models import UserProfile


def ai_data_endpoint(request):
    """
    Endpoint específico para motores de IA
    Proporciona datos estructurados sobre empresas y reseñas
    """
    # Obtener estadísticas generales
    total_companies = Company.objects.filter(is_active=True).count()
    total_reviews = Review.objects.filter(status='approved').count()
    total_candidates = UserProfile.objects.filter(role='candidate').count()
    
    # Top empresas por calificación
    top_companies = Company.objects.filter(
        is_active=True,
        reviews__status='approved'
    ).annotate(
        avg_rating=Avg('reviews__overall_rating'),
        review_count=Count('reviews')
    ).filter(
        review_count__gte=1
    ).order_by('-avg_rating', '-review_count')[:10]
    
    # Distribución por sectores
    sector_stats = Company.objects.filter(is_active=True).values('sector').annotate(
        count=Count('id'),
        avg_rating=Avg('reviews__overall_rating'),
        total_reviews=Count('reviews')
    ).order_by('-count')
    
    # Distribución por ubicación
    location_stats = Company.objects.filter(is_active=True).values('location').annotate(
        count=Count('id'),
        avg_rating=Avg('reviews__overall_rating')
    ).order_by('-count')[:10]
    
    # Datos estructurados para IA
    ai_data = {
        "platform_info": {
            "name": "SelecLoop",
            "description": "Plataforma colaborativa para compartir reseñas anónimas sobre procesos de selección laboral",
            "language": "Spanish",
            "target_audience": "Job seekers, candidates, professionals",
            "content_type": "Job selection process reviews and company feedback",
            "geo_coverage": "Colombia and Latin America",
            "data_format": "structured-json",
            "ai_accessible": True
        },
        "statistics": {
            "total_companies": total_companies,
            "total_reviews": total_reviews,
            "total_candidates": total_candidates,
            "average_rating": Review.objects.filter(status='approved').aggregate(
                avg=Avg('overall_rating')
            )['avg'] or 0
        },
        "top_companies": [
            {
                "name": company.name,
                "location": company.location,
                "region": company.region,
                "country": company.country,
                "sector": company.sector,
                "average_rating": round(company.avg_rating, 1),
                "review_count": company.review_count
            }
            for company in top_companies
        ],
        "sector_distribution": [
            {
                "sector": stat['sector'] or 'Sin especificar',
                "company_count": stat['count'],
                "average_rating": round(stat['avg_rating'] or 0, 1),
                "total_reviews": stat['total_reviews']
            }
            for stat in sector_stats
        ],
        "location_distribution": [
            {
                "location": stat['location'] or 'Sin especificar',
                "company_count": stat['count'],
                "average_rating": round(stat['avg_rating'] or 0, 1),
                "country": "Colombia"
            }
            for stat in location_stats
        ],
        "data_structure": {
            "review_fields": [
                "job_title", "modality", "overall_rating", "communication_rating",
                "difficulty_rating", "response_time_rating", "pros", "cons",
                "interview_questions", "submission_date", "status"
            ],
            "company_fields": [
                "name", "location", "region", "country", "sector", "description", 
                "website"
            ],
            "modality_types": ["presencial", "remoto", "híbrido"],
            "rating_scale": "1-5 stars",
            "review_status": ["pending", "approved", "rejected"]
        }
    }
    
    return JsonResponse(ai_data, json_dumps_params={'indent': 2, 'ensure_ascii': False})


def company_ai_data(request, company_id):
    """
    Datos estructurados específicos de una empresa para IA
    """
    try:
        company = Company.objects.get(id=company_id, is_active=True)
        
        # Reseñas aprobadas de la empresa
        reviews = Review.objects.filter(
            company=company,
            status='approved'
        ).select_related('user_profile__user')
        
        # Estadísticas de la empresa
        stats = {
            'total_reviews': reviews.count(),
            'average_rating': reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0,
            'communication_avg': reviews.aggregate(avg=Avg('communication_rating'))['avg'] or 0,
            'difficulty_avg': reviews.aggregate(avg=Avg('difficulty_rating'))['avg'] or 0,
            'response_time_avg': reviews.aggregate(avg=Avg('response_time_rating'))['avg'] or 0
        }
        
        # Distribución por modalidad
        modality_distribution = reviews.values('modality').annotate(
            count=Count('id'),
            avg_rating=Avg('overall_rating')
        ).order_by('-count')
        
        # Distribución por cargo
        job_title_distribution = reviews.values('job_title').annotate(
            count=Count('id'),
            avg_rating=Avg('overall_rating')
        ).order_by('-count')[:10]
        
        # Datos estructurados para IA
        company_ai_data = {
            "company_info": {
                "name": company.name,
                "location": company.location,
                "region": company.region,
                "country": company.country,
                "sector": company.sector,
                "description": company.description,
                "website": company.website,
                "is_active": company.is_active,
                "geo_data": {
                    "address": f"{company.location}, {company.country}"
                }
            },
            "statistics": {
                "total_reviews": stats['total_reviews'],
                "average_rating": round(stats['average_rating'], 1),
                "communication_rating": stats['communication_avg'],
                "difficulty_rating": stats['difficulty_avg'],
                "response_time_rating": stats['response_time_avg']
            },
            "modality_distribution": [
                {
                    "modality": mod['modality'],
                    "count": mod['count'],
                    "average_rating": round(mod['avg_rating'], 1)
                }
                for mod in modality_distribution
            ],
            "job_title_distribution": [
                {
                    "job_title": job['job_title'],
                    "count": job['count'],
                    "average_rating": round(job['avg_rating'], 1)
                }
                for job in job_title_distribution
            ],
            "recent_reviews": [
                {
                    "job_title": review.job_title,
                    "modality": review.modality,
                    "overall_rating": review.overall_rating,
                    "communication_rating": review.communication_rating,
                    "difficulty_rating": review.difficulty_rating,
                    "response_time_rating": review.response_time_rating,
                    "pros": review.pros,
                    "cons": review.cons,
                    "interview_questions": review.interview_questions,
                    "submission_date": review.submission_date.isoformat()
                }
                for review in reviews.order_by('-submission_date')[:5]
            ]
        }
        
        return JsonResponse(company_ai_data, json_dumps_params={'indent': 2, 'ensure_ascii': False})
        
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company not found'}, status=404)


def reviews_ai_data(request):
    """
    Datos estructurados de todas las reseñas para IA
    """
    # Parámetros de filtro
    company_id = request.GET.get('company_id')
    sector = request.GET.get('sector')
    location = request.GET.get('location')
    modality = request.GET.get('modality')
    min_rating = request.GET.get('min_rating')
    
    # Base query
    reviews = Review.objects.filter(status='approved').select_related(
        'company', 'user_profile__user'
    )
    
    # Aplicar filtros
    if company_id:
        reviews = reviews.filter(company_id=company_id)
    if sector:
        reviews = reviews.filter(company__sector__icontains=sector)
    if location:
        reviews = reviews.filter(company__location__icontains=location)
    if modality:
        reviews = reviews.filter(modality=modality)
    if min_rating:
        reviews = reviews.filter(overall_rating__gte=int(min_rating))
    
    # Limitar resultados para evitar respuestas muy grandes
    reviews = reviews.order_by('-submission_date')[:100]
    
    # Datos estructurados
    reviews_data = {
        "reviews": [
            {
                "company": {
                    "name": review.company.name,
                    "location": review.company.location,
                    "region": review.company.region,
                    "sector": review.company.sector,
                    "country": review.company.country
                },
                "review": {
                    "job_title": review.job_title,
                    "modality": review.modality,
                    "overall_rating": review.overall_rating,
                    "communication_rating": review.communication_rating,
                    "difficulty_rating": review.difficulty_rating,
                    "response_time_rating": review.response_time_rating,
                    "pros": review.pros,
                    "cons": review.cons,
                    "interview_questions": review.interview_questions,
                    "submission_date": review.submission_date.isoformat()
                }
            }
            for review in reviews
        ],
        "filters_applied": {
            "company_id": company_id,
            "sector": sector,
            "location": location,
            "modality": modality,
            "min_rating": min_rating
        },
        "total_results": reviews.count()
    }
    
    return JsonResponse(reviews_data, json_dumps_params={'indent': 2, 'ensure_ascii': False})