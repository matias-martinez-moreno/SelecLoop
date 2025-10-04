# =============================================================================
# VISTAS DE LA APLICACIÓN ACCOUNTS - SelecLoop
# =============================================================================
# Este archivo contiene las vistas relacionadas con usuarios y autenticación
#
# Vistas principales:
# - login_view: Autenticación de usuarios
# - logout_view: Cerrar sesión
# - my_profile_view: Perfil del usuario
# - update_profile_view: Actualizar perfil
# =============================================================================

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from .models import UserProfile, OnboardingStatus
from .forms import ProfileUpdateForm


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


@login_required
def my_profile_view(request):
    """Vista para mostrar el perfil del usuario"""
    user_profile = request.user.profile
    
    if user_profile.role == 'candidate':
        # Importar modelos necesarios
        from reviews.models import Review, PendingReview
        from work_history.models import WorkHistory
        from achievements.models import UserAchievement
        
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