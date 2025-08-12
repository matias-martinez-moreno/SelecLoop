# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.db.models import Avg, Count
from .models import Company, Review, UserProfile 


def root_redirect_view(request):
    if request.user.is_authenticated:
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        print(f"DEBUG: root_redirect_view - Usuario: {request.user.username}, Rol: {user_profile.role}")

        if user_profile.role == 'company_rep':
            return redirect('company_dashboard')
        else: 
            return redirect('dashboard')
    else:
        return redirect('login')

# --- Vista de Login ---
def login_view(request):
    if request.user.is_authenticated:
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        print(f"DEBUG: login_view (already authenticated) - Usuario: {request.user.username}, Rol: {user_profile.role}")

        if user_profile.role == 'company_rep':
            return redirect('company_dashboard')
        else:
            return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            
            print(f"DEBUG: login_view (POST success) - Usuario: {user.username}, Rol: {user_profile.role}")

            if user_profile.role == 'company_rep':
                return redirect('company_dashboard')
            else:
                return redirect('dashboard')
        else:
            context = {
                'title': 'Iniciar Sesión',
                'error_message': 'Nombre de usuario o contraseña incorrectos.'
            }
            return render(request, 'core/login.html', context)
        
    context = {'title': 'Iniciar Sesión'}
    return render(request, 'core/login.html', context)


@login_required
def dashboard_view(request):
    # Si el usuario es un representante de empresa, lo redirigimos a su panel
    if hasattr(request.user, 'profile') and request.user.profile.role == 'company_rep':
        print(f"DEBUG: dashboard_view - Redirigiendo a company_dashboard para {request.user.username}")
        return redirect('company_dashboard')

    companies = Company.objects.filter(is_active=True).annotate(
        avg_rating=Avg('reviews__overall_rating'),
        total_reviews=Count('reviews')
    )
    
    search_query = request.GET.get('search', '')
    selected_sector = request.GET.get('sector', '')
    selected_location = request.GET.get('location', '')
    selected_modality = request.GET.get('modality', '')

    if search_query:
        companies = companies.filter(name__icontains=search_query)
    
    if selected_sector:
        companies = companies.filter(sector__iexact=selected_sector)
    
    if selected_location:
        companies = companies.filter(location__iexact=selected_location)

    if selected_modality:
        companies = companies.filter(reviews__modality=selected_modality).distinct()

    unique_sectors = Company.objects.values_list('sector', flat=True).distinct()
    unique_locations = Company.objects.values_list('location', flat=True).distinct()
    unique_modalities = [choice[0] for choice in Review.MODALITY_CHOICES]

    context = {
        'title': 'Dashboard - SelecLoop',
        'companies': companies,
        'total_companies': companies.count(),
        'search_query': search_query,
        'selected_sector': selected_sector,
        'selected_location': selected_location,
        'selected_modality': selected_modality,
        'unique_sectors': unique_sectors,
        'unique_locations': unique_locations,
        'unique_modalities': unique_modalities,
    }
    return render(request, 'core/index.html', context)


@login_required
def company_dashboard_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'company_rep':
        print(f"DEBUG: company_dashboard_view - Redirigiendo a dashboard para {request.user.username} (rol incorrecto)")
        return redirect('dashboard')

    user_profile = request.user.profile
    company = user_profile.company

    if not company:
        context = {'title': 'Panel de Empresa', 'error_message': 'Tu perfil no está asociado a ninguna empresa.'}
        return render(request, 'core/company_dashboard.html', context)

    reviews = Review.objects.filter(company=company, is_approved=True).order_by('-submission_date')
    
    avg_overall_rating = reviews.aggregate(Avg('overall_rating'))['overall_rating__avg']
    total_reviews = reviews.count()

    context = {
        'title': f'Panel de {company.name}',
        'company': company,
        'reviews': reviews,
        'avg_overall_rating': avg_overall_rating,
        'total_reviews': total_reviews,
    }
    return render(request, 'core/company_dashboard.html', context)


@login_required
def company_detail_view(request, pk):
    if hasattr(request.user, 'profile') and request.user.profile.role == 'company_rep':
        return redirect('company_dashboard')

    company = get_object_or_404(Company, pk=pk)
    
    user_has_contributed = False
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'candidate':
        user_profile = request.user.profile
        user_has_contributed = Review.objects.filter(company=company, user_profile=user_profile).exists()

    reviews = []
    if user_has_contributed:
        reviews = company.reviews.filter(is_approved=True)

    context = {
        'title': f'Detalle de {company.name}',
        'company': company,
        'reviews': reviews,
        'user_has_contributed': user_has_contributed,
    }
    return render(request, 'core/company_detail.html', context)

@login_required
def create_review_view(request):
    if hasattr(request.user, 'profile') and request.user.profile.role != 'candidate':
        return redirect('dashboard')

    context = {'title': 'Crear Reseña'}
    return render(request, 'core/create_review.html', context)

@login_required
def my_reviews_view(request):
    if hasattr(request.user, 'profile') and request.user.profile.role != 'candidate':
        return redirect('dashboard')

    context = {'title': 'Mis Reseñas'}
    return render(request, 'core/my_reviews.html', context)

@login_required
def profile_view(request):
    context = {'title': 'Mi Perfil'}
    return render(request, 'core/profile.html', context)