# =============================================================================
# FORMULARIOS DE LA APLICACIÓN ACCOUNTS - SelecLoop
# =============================================================================
# Este archivo define formularios relacionados con usuarios y autenticación
#
# Formularios:
# - UserCreationForm: Registro de nuevos usuarios
# - ProfileUpdateForm: Actualización de perfil de usuario
# =============================================================================

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


# ===== FORMULARIO: CREACIÓN DE USUARIOS =====
class UserCreationForm(UserCreationForm):
    """
    Formulario personalizado para crear nuevos usuarios.
    Extiende el formulario estándar de Django con campos adicionales.
    """
    
    # ===== CAMPOS ADICIONALES =====
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        label="Nombre",
        help_text="Nombre real del usuario"
    )
    
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        label="Apellido",
        help_text="Apellido real del usuario"
    )
    
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        help_text="Correo electrónico válido del usuario"
    )
    
    # ===== CONFIGURACIÓN DEL FORMULARIO =====
    class Meta:
        """Configuración del formulario"""
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def clean_email(self):
        """Valida que el email sea único en el sistema"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def save(self, commit=True):
        """Guarda el usuario y crea automáticamente su perfil"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


# ===== FORMULARIO: ACTUALIZAR PERFIL =====
class ProfileUpdateForm(forms.Form):
    """Formulario para actualizar perfil de usuario con información profesional."""

    first_name = forms.CharField(
        max_length=30,
        required=False,
        label="Nombre"
    )

    last_name = forms.CharField(
        max_length=30,
        required=False,
        label="Apellido"
    )

    avatar = forms.ImageField(
        required=False,
        label="Foto de perfil (opcional)"
    )
    
    remove_avatar = forms.BooleanField(
        required=False,
        label="Quitar foto de perfil"
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Teléfono",
        help_text="Número de contacto"
    )
    
    email = forms.EmailField(
        required=False,
        label="Correo electrónico",
        help_text="Correo electrónico de contacto"
    )
    
    linkedin_url = forms.URLField(
        max_length=200,
        required=False,
        label="LinkedIn",
        help_text="URL de tu perfil de LinkedIn (ej: https://linkedin.com/in/tu-perfil)",
        widget=forms.URLInput(attrs={'placeholder': 'https://linkedin.com/in/tu-perfil'})
    )
    
    availability_status = forms.ChoiceField(
        choices=UserProfile.AVAILABILITY_CHOICES,
        required=False,
        label="¿Estás buscando empleo?",
        help_text="Tu disponibilidad laboral actual"
    )
    
    bio = forms.CharField(
        required=False,
        label="Biografía",
        help_text="Información sobre ti, tu experiencia y objetivos profesionales",
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Cuéntanos sobre ti...'})
    )
    
    city = forms.CharField(
        max_length=100,
        required=False,
        label="Ciudad",
        help_text="Ciudad donde resides"
    )
    
    country = forms.CharField(
        max_length=100,
        required=False,
        label="País",
        help_text="País donde resides"
    )
    
    years_of_experience = forms.IntegerField(
        required=False,
        label="Años de experiencia",
        help_text="Años de experiencia profesional",
        min_value=0,
        max_value=100
    )
    
    specialization = forms.CharField(
        max_length=200,
        required=False,
        label="Especialización",
        help_text="Tu área de especialización profesional (ej: Desarrollo Web, Marketing Digital)"
    )
    
    languages = forms.CharField(
        max_length=200,
        required=False,
        label="Idiomas",
        help_text="Idiomas que manejas (ej: Español, Inglés, Francés)"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        # Extraer initial de kwargs ANTES de llamar a super()
        initial_data = kwargs.pop('initial', {})
        
        # Si no hay datos POST (args está vacío) y hay usuario, precargar desde el usuario
        if not args and self.user:
            profile = self.user.profile
            # Si no hay initial_data, crear uno desde el usuario
            if not initial_data:
                initial_data = {}
            # Solo precargar si el campo no está ya en initial_data
            if 'first_name' not in initial_data:
                initial_data['first_name'] = self.user.first_name or ''
            if 'last_name' not in initial_data:
                initial_data['last_name'] = self.user.last_name or ''
            if 'phone' not in initial_data:
                initial_data['phone'] = profile.phone or ''
            if 'email' not in initial_data:
                initial_data['email'] = self.user.email or ''
            if 'linkedin_url' not in initial_data:
                initial_data['linkedin_url'] = profile.linkedin_url or ''
            if 'availability_status' not in initial_data:
                initial_data['availability_status'] = profile.availability_status or ''
            if 'bio' not in initial_data:
                initial_data['bio'] = profile.bio or ''
            if 'city' not in initial_data:
                initial_data['city'] = profile.city or ''
            if 'country' not in initial_data:
                initial_data['country'] = profile.country or ''
            if 'years_of_experience' not in initial_data:
                initial_data['years_of_experience'] = profile.years_of_experience or ''
            if 'specialization' not in initial_data:
                initial_data['specialization'] = profile.specialization or ''
            if 'languages' not in initial_data:
                initial_data['languages'] = profile.languages or ''
        
        # Agregar initial_data a kwargs
        if initial_data:
            kwargs['initial'] = initial_data
        
        # Llamar a super() PRIMERO para que self.fields esté disponible
        super().__init__(*args, **kwargs)
        
        # Para company_rep y staff, ocultar campos que no necesita
        # Los candidatos pueden editar todos los campos
        if self.user and hasattr(self.user, 'profile') and self.user.profile.role in ['company_rep', 'staff']:
            # Ocultar campos que no son necesarios para company_rep y staff
            self.fields.pop('linkedin_url', None)
            self.fields.pop('availability_status', None)
            self.fields.pop('bio', None)
            self.fields.pop('city', None)
            self.fields.pop('country', None)
            self.fields.pop('years_of_experience', None)
            self.fields.pop('specialization', None)
            self.fields.pop('languages', None)
            # Para company_rep y staff, mantener phone y email visibles
        
        # Estilos para campos de formulario
        for field_name, field in self.fields.items():
            if field_name == 'avatar':
                field.widget.attrs.update({'class': 'form-control', 'accept': 'image/*'})
            elif field_name == 'remove_avatar':
                field.widget.attrs.update({'class': 'form-check-input'})
            elif field_name == 'bio':
                field.widget.attrs.update({'class': 'form-control', 'rows': '4'})
            elif field_name == 'availability_status':
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def save(self):
        if not self.user:
            return
        # Actualizar datos del usuario
        self.user.first_name = self.cleaned_data.get('first_name', '')
        self.user.last_name = self.cleaned_data.get('last_name', '')
        email = self.cleaned_data.get('email', '')
        if email:
            self.user.email = email
        self.user.save()

        # Asegurar profile y actualizar campos
        profile: UserProfile = self.user.profile
        phone = self.cleaned_data.get('phone', '')
        if phone:
            profile.phone = phone
        
        # Solo actualizar estos campos si el usuario no es company_rep ni staff
        if not (hasattr(self.user, 'profile') and self.user.profile.role in ['company_rep', 'staff']):
            profile.linkedin_url = self.cleaned_data.get('linkedin_url', '') or None
            profile.availability_status = self.cleaned_data.get('availability_status', '') or None
            profile.bio = self.cleaned_data.get('bio', '') or None
            profile.city = self.cleaned_data.get('city', '') or None
            profile.country = self.cleaned_data.get('country', '') or None
            years_exp = self.cleaned_data.get('years_of_experience')
            profile.years_of_experience = years_exp if years_exp is not None and years_exp != '' else None
            profile.specialization = self.cleaned_data.get('specialization', '') or None
            profile.languages = self.cleaned_data.get('languages', '') or None
        
        # Manejar la foto de perfil
        remove_avatar = self.cleaned_data.get('remove_avatar', False)
        if remove_avatar:
            profile.avatar.delete(save=False)
            profile.avatar = None
        else:
            avatar_file = self.cleaned_data.get('avatar')
            if avatar_file:
                profile.avatar = avatar_file
        
        profile.save()
