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
from django.db.models import Q
from .models import UserProfile, OnboardingStatus
from .forms import ProfileUpdateForm


def login_view(request):
    """Vista de login - autentica usuarios y redirige según rol"""
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        # Intentar autenticar primero con username
        user = authenticate(request, username=username_or_email, password=password)
        
        # Si falla, intentar buscar por email
        if user is None:
            try:
                user_by_email = User.objects.get(email=username_or_email)
                # Autenticar con el username real del usuario
                user = authenticate(request, username=user_by_email.username, password=password)
            except User.DoesNotExist:
                user = None
            except User.MultipleObjectsReturned:
                # Si hay múltiples usuarios con el mismo email, intentar con el primero
                user_by_email = User.objects.filter(email=username_or_email).first()
                if user_by_email:
                    user = authenticate(request, username=user_by_email.username, password=password)
                else:
                    user = None
        
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


def get_user_badge(user_profile):
    """
    Determina el badge del usuario basado en sus logros obtenidos.
    Retorna un diccionario con nombre, icono y color del badge.
    """
    if user_profile.role != 'candidate':
        return None
    
    from achievements.models import UserAchievement
    from reviews.models import Review
    
    achievement_count = UserAchievement.objects.filter(user_profile=user_profile).count()
    total_reviews = Review.objects.filter(user_profile=user_profile).count()
    
    # Determinar badge basado en logros y reseñas
    if achievement_count >= 10 or total_reviews >= 20:
        return {
            'name': 'Leyenda',
            'icon': 'fas fa-crown',
            'color': 'warning',
            'bg_color': 'bg-warning',
            'text_color': 'text-dark'
        }
    elif achievement_count >= 6 or total_reviews >= 10:
        return {
            'name': 'Maestro',
            'icon': 'fas fa-trophy',
            'color': 'warning',
            'bg_color': 'bg-warning',
            'text_color': 'text-dark'
        }
    elif achievement_count >= 3 or total_reviews >= 5:
        return {
            'name': 'Experto',
            'icon': 'fas fa-star',
            'color': 'info',
            'bg_color': 'bg-info',
            'text_color': 'text-white'
        }
    elif achievement_count >= 1 or total_reviews >= 1:
        return {
            'name': 'Novato',
            'icon': 'fas fa-seedling',
            'color': 'success',
            'bg_color': 'bg-success',
            'text_color': 'text-white'
        }
    else:
        return {
            'name': 'Principiante',
            'icon': 'fas fa-circle',
            'color': 'secondary',
            'bg_color': 'bg-secondary',
            'text_color': 'text-white'
        }


@login_required
def my_profile_view(request):
    """Vista para mostrar el perfil del usuario"""
    user_profile = request.user.profile
    
    # Obtener badge del usuario
    user_badge = get_user_badge(user_profile)
    
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
        
        # Últimas 3 reseñas para el perfil
        latest_reviews = Review.objects.filter(
            user_profile=user_profile
        ).select_related('company').order_by('-submission_date')[:3]
        
        # Contar logros obtenidos
        achievement_count = UserAchievement.objects.filter(user_profile=user_profile).count()
        user_achievements = UserAchievement.objects.filter(user_profile=user_profile).select_related('achievement').order_by('-earned_at')
        
        # Estadísticas adicionales para logros
        companies_reviewed = Review.objects.filter(user_profile=user_profile).values('company').distinct().count()
        work_experiences = WorkHistory.objects.filter(user_profile=user_profile).count()
        
        context = {
            'user_profile': user_profile,
            'user_badge': user_badge,
            'total_reviews': total_reviews,
            'approved_reviews': approved_reviews,
            'pending_approval': pending_approval,
            'pending_reviews': pending_reviews,
            'work_history': work_history,
            'latest_reviews': latest_reviews,
            'achievement_count': achievement_count,
            'user_achievements': user_achievements,
            'companies_reviewed': companies_reviewed,
            'work_experiences': work_experiences,
            'show_stats': True,
        }
    else:
        context = {
            'user_profile': user_profile,
            'user_badge': user_badge,
            'show_stats': False,
        }
    
    return render(request, 'core/profile.html', context)


@login_required
def view_user_profile_view(request, user_id):
    """Vista para que cualquier usuario autenticado pueda ver el perfil de otro usuario"""
    from django.contrib.auth.models import User
    
    try:
        target_user = User.objects.get(id=user_id)
        target_profile = target_user.profile
        
        # No permitir ver tu propio perfil desde esta vista (deben usar my_profile)
        if target_user.id == request.user.id:
            return redirect('my_profile')
            
    except User.DoesNotExist:
        messages.error(request, '❌ Usuario no encontrado.')
        return redirect('dashboard')
    
    # Obtener badge del usuario
    user_badge = get_user_badge(target_profile)
    
    # Obtener información del usuario
    from reviews.models import Review
    from work_history.models import WorkHistory
    from achievements.models import UserAchievement
    
    # Estadísticas del usuario
    total_reviews = Review.objects.filter(user_profile=target_profile).count()
    approved_reviews = Review.objects.filter(
        user_profile=target_profile,
        status='approved'
    ).count()
    rejected_reviews = Review.objects.filter(
        user_profile=target_profile,
        status='rejected'
    ).count()
    pending_reviews = Review.objects.filter(
        user_profile=target_profile,
        status='pending'
    ).count()
    
    # Últimas reseñas
    latest_reviews = Review.objects.filter(
        user_profile=target_profile
    ).select_related('company').order_by('-submission_date')[:5]
    
    # Historial laboral
    work_history = WorkHistory.objects.filter(
        user_profile=target_profile
    ).select_related('company').order_by('-start_date')
    
    # Logros
    achievement_count = UserAchievement.objects.filter(user_profile=target_profile).count()
    user_achievements = UserAchievement.objects.filter(
        user_profile=target_profile
    ).select_related('achievement').order_by('-earned_at')[:10]
    
    # Empresas reseñadas
    companies_reviewed = Review.objects.filter(
        user_profile=target_profile
    ).values('company').distinct().count()
    
    context = {
        'user_profile': target_profile,
        'target_user': target_user,
        'user_badge': user_badge,
        'total_reviews': total_reviews,
        'approved_reviews': approved_reviews,
        'rejected_reviews': rejected_reviews,
        'pending_reviews': pending_reviews,
        'latest_reviews': latest_reviews,
        'work_history': work_history,
        'achievement_count': achievement_count,
        'user_achievements': user_achievements,
        'companies_reviewed': companies_reviewed,
        'is_viewing_other_profile': True,  # Flag para indicar que es perfil de otro usuario
    }
    
    return render(request, 'core/view_user_profile.html', context)


@login_required
def update_profile_view(request):
    """Permite al usuario actualizar su nombre visible y foto."""
    user = request.user
    initial = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': getattr(user.profile, 'phone', ''),
        'city': getattr(user.profile, 'city', ''),
        'country': getattr(user.profile, 'country', ''),
        'linkedin_url': getattr(user.profile, 'linkedin_url', ''),
        'portfolio_url': getattr(user.profile, 'portfolio_url', ''),
        'years_of_experience': getattr(user.profile, 'years_of_experience', None),
        'specialization': getattr(user.profile, 'specialization', ''),
        'languages': getattr(user.profile, 'languages', ''),
        'availability_status': getattr(user.profile, 'availability_status', ''),
        'bio': getattr(user.profile, 'bio', ''),
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
                'phone': 'El teléfono debe ser válido.',
                'city': 'La ciudad debe tener máximo 100 caracteres.',
                'country': 'El país debe tener máximo 100 caracteres.',
                'linkedin_url': 'La URL de LinkedIn debe ser válida.',
                'portfolio_url': 'La URL del portfolio debe ser válida.',
                'years_of_experience': 'Los años de experiencia deben ser un número entre 0 y 100.',
                'specialization': 'La especialización debe tener máximo 200 caracteres.',
                'languages': 'Los idiomas deben tener máximo 200 caracteres.',
                'availability_status': 'Debes seleccionar una opción de disponibilidad válida.',
                'bio': 'La biografía debe tener un formato válido.',
                'avatar': 'La imagen debe ser válida (JPG, PNG). Tamaño máximo recomendado: 2MB.'
            }
            
            for field, errors in form.errors.items():
                field_name = error_messages.get(field, field.replace('_', ' ').title())
                for error in errors:
                    messages.error(request, f'❌ {field_name}: {error}')
    else:
        form = ProfileUpdateForm(initial=initial, user=user)

    return render(request, 'core/profile_update.html', {'form': form})


def password_reset_request_view(request):
    """Vista para solicitar recuperación de contraseña"""
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email', '').strip()
        
        if not username_or_email:
            messages.error(request, '❌ Por favor, ingresa tu nombre de usuario o correo electrónico.')
            return render(request, 'core/password_reset_request.html')
        
        # Buscar usuario por username o email
        try:
            user = User.objects.get(
                Q(username=username_or_email) | Q(email=username_or_email)
            )
            # Redirigir a la página de confirmación (sin enviar correo realmente)
            return redirect('password_reset_confirm')
        except User.DoesNotExist:
            # Por seguridad, mostrar el mismo mensaje aunque el usuario no exista
            messages.info(request, 'Si el usuario o correo existe, recibirás un correo con las instrucciones.')
            return redirect('password_reset_confirm')
        except User.MultipleObjectsReturned:
            # Si hay múltiples usuarios, también redirigir a confirmación
            return redirect('password_reset_confirm')
    
    return render(request, 'core/password_reset_request.html')


def password_reset_confirm_view(request):
    """Vista de confirmación de que se envió el correo"""
    return render(request, 'core/password_reset_confirm.html')