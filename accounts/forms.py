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
    """Formulario para actualizar nombre visible y foto de perfil."""

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

    display_name = forms.CharField(
        max_length=100,
        required=False,
        label="Nombre visible"
    )

    avatar = forms.ImageField(
        required=False,
        label="Foto de perfil (opcional)"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def save(self):
        if not self.user:
            return
        # Actualizar datos del usuario
        self.user.first_name = self.cleaned_data.get('first_name', '')
        self.user.last_name = self.cleaned_data.get('last_name', '')
        self.user.save()

        # Asegurar profile
        profile: UserProfile = self.user.profile
        profile.display_name = self.cleaned_data.get('display_name', '')
        avatar_file = self.cleaned_data.get('avatar')
        if avatar_file:
            profile.avatar = avatar_file
        profile.save()
