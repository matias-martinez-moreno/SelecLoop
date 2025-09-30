# =============================================================================
# FORMULARIOS DE LA APLICACIÓN - SelecLoop
# =============================================================================
# Este archivo define todos los formularios utilizados en SelecLoop
# Cada formulario está conectado a un modelo específico y maneja validación
#
# Arquitectura: Formularios basados en ModelForm de Django
# Patrón: Form-Object Pattern con validación automática
#
# Formularios principales:
# - ReviewForm: Creación y edición de reseñas con calificaciones
# - UserCreationForm: Registro de nuevos usuarios
# - ProfileUpdateForm: Actualización de perfil de usuario
# - StaffAssignmentForm: Asignación de empresas por staff
#
# Características:
# - Validación frontend y backend
# - Protección CSRF automática
# - Integración con Bootstrap para estilos
# - Manejo de archivos (imágenes en reseñas)
# =============================================================================

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Review, UserProfile, WorkHistory

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

# =============================================================================
# FORMULARIO: CREACIÓN DE RESEÑAS
# =============================================================================
# Formulario principal para crear y editar reseñas de procesos de selección
# Permite a los candidatos evaluar su experiencia en empresas con calificaciones
#
# Características principales:
# - Sistema de calificaciones múltiple (comunicación, dificultad, tiempo de respuesta)
# - Campos opcionales (preguntas de entrevista, imagen)
# - Validación automática de rangos de calificación
# - Integración con Bootstrap para UI responsive
# - Protección contra spam y validación de datos
#
# Funcionalidades SEO/Geo:
# - Campos de empresa incluyen información geo-localizada
# - Validación de datos para structured data
# =============================================================================
class ReviewForm(forms.ModelForm):
    """
    Formulario para crear y editar reseñas de procesos de selección.
    Permite a los candidatos evaluar su experiencia en empresas con
    sistema de calificaciones múltiple y campos opcionales.
    """
    
    # ===== CAMPOS PERSONALIZADOS =====
    company = forms.ModelChoiceField(
        queryset=None,  # Se establece dinámicamente en la vista
        label="Empresa",
        help_text="Selecciona la empresa donde participaste en el proceso de selección"
    )
    
    job_title = forms.CharField(
        max_length=200,
        label="Cargo o puesto",
        help_text="Título del trabajo o puesto al que te postulaste",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Desarrollador Frontend, Analista de Datos...'
        })
    )
    
    # ===== CAMPOS DE MODALIDAD =====
    modality = forms.ChoiceField(
        choices=[
            ('presencial', 'Presencial'),
            ('remoto', 'Remoto'),
            ('híbrido', 'Híbrido'),
        ],
        label="Modalidad de trabajo",
        help_text="Tipo de trabajo ofrecido por la empresa",
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    # ===== CAMPOS DE CALIFICACIÓN =====
    communication_rating = forms.ChoiceField(
        choices=[
            ('excellent', 'Excelente'),
            ('good', 'Buena'),
            ('regular', 'Regular'),
            ('poor', 'Mala'),
        ],
        label="Calificación de comunicación",
        help_text="¿Qué tan clara fue la comunicación durante el proceso?",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    difficulty_rating = forms.ChoiceField(
        choices=[
            ('very_easy', 'Muy Fácil'),
            ('easy', 'Fácil'),
            ('moderate', 'Moderada'),
            ('difficult', 'Difícil'),
            ('very_difficult', 'Muy Difícil'),
        ],
        label="Calificación de dificultad",
        help_text="¿Qué tan desafiante fue el proceso de selección?",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    response_time_rating = forms.ChoiceField(
        choices=[
            ('immediate', 'Inmediata'),
            ('same_day', 'Mismo día'),
            ('next_day', 'Al día siguiente'),
            ('few_days', 'En pocos días'),
            ('slow', 'Lenta'),
        ],
        label="Calificación de tiempo de respuesta",
        help_text="¿Qué tan rápido respondieron a tus consultas?",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    overall_rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        label="Calificación general",
        help_text="Calificación general del 1 al 5",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '5'
        })
    )
    
    # ===== CAMPOS DE CONTENIDO =====
    pros = forms.CharField(
        label="Aspectos positivos",
        help_text="¿Qué te gustó del proceso? ¿Qué hicieron bien?",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe los aspectos positivos del proceso de selección...'
        })
    )
    
    cons = forms.CharField(
        label="Aspectos a mejorar",
        help_text="¿Qué podrían mejorar? ¿Qué no te gustó?",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe los aspectos que podrían mejorar...'
        })
    )
    
    interview_questions = forms.CharField(
        label="Preguntas de entrevista",
        help_text="¿Qué preguntas te hicieron? Esto ayudará a otros candidatos a prepararse.",
        required=False,  # Campo opcional
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Comparte las preguntas que te hicieron durante la entrevista...'
        })
    )

    # ===== IMAGEN OPCIONAL =====
    image = forms.ImageField(
        required=False,
        label="Imagen (opcional)",
        help_text="Adjunta una imagen relacionada con tu experiencia"
    )
    
    # ===== CONFIGURACIÓN DEL FORMULARIO =====
    class Meta:
        """Configuración del formulario"""
        model = Review
        fields = [
            'company', 'job_title', 'modality', 'communication_rating',
            'difficulty_rating', 'response_time_rating', 'overall_rating',
            'pros', 'cons', 'interview_questions', 'image'
        ]
    
    def __init__(self, *args, **kwargs):
        """Inicializa el formulario con configuraciones personalizadas"""
        super().__init__(*args, **kwargs)
        
        # Personalizar widgets para mejor presentación
        for field_name, field in self.fields.items():
            if field_name not in ['modality']:  # Excluir campos de radio
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        """Validación personalizada del formulario"""
        cleaned_data = super().clean()
        
        # Validar que la calificación general esté en el rango correcto
        overall_rating = cleaned_data.get('overall_rating')
        if overall_rating and (overall_rating < 1 or overall_rating > 5):
            raise forms.ValidationError('La calificación general debe estar entre 1 y 5.')
        
        return cleaned_data

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

# ===== FORMULARIO: ASIGNACIÓN DE EMPRESAS POR STAFF =====
class WorkHistoryForm(forms.ModelForm):
    """
    Formulario para agregar y editar historial laboral del usuario.
    Permite a los candidatos agregar empresas donde han trabajado.
    """
    
    # ===== CAMPOS DE RELACIÓN =====
    company = forms.ModelChoiceField(
        queryset=None,  # Se establece dinámicamente en la vista
        label="Empresa",
        help_text="Selecciona la empresa donde trabajaste o trabajas",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # ===== CAMPOS BÁSICOS =====
    job_title = forms.CharField(
        max_length=200,
        label="Cargo o puesto",
        help_text="Título del trabajo o puesto que desempeñaste",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Desarrollador Frontend, Analista de Datos...'
        })
    )
    
    start_date = forms.DateField(
        label="Fecha de inicio",
        help_text="Fecha en que comenzaste a trabajar en esta empresa",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    end_date = forms.DateField(
        label="Fecha de finalización",
        help_text="Fecha en que terminaste de trabajar (deja vacío si aún trabajas aquí)",
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    # ===== CAMPOS DE ESTADO =====
    is_current_job = forms.BooleanField(
        label="Trabajo actual",
        help_text="Marca esta casilla si actualmente trabajas en esta empresa",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        """Configuración del formulario"""
        model = WorkHistory
        fields = ['company', 'job_title', 'start_date', 'end_date', 'is_current_job']
    
    def __init__(self, *args, **kwargs):
        """Inicialización del formulario"""
        super().__init__(*args, **kwargs)
        
        # Establecer queryset de empresas activas
        self.fields['company'].queryset = Company.objects.filter(is_active=True)
    
    def clean(self):
        """Validación personalizada del formulario"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_current_job = cleaned_data.get('is_current_job')
        
        # Validar fechas
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("La fecha de inicio no puede ser posterior a la fecha de finalización.")
        
        # Si es trabajo actual, no debe tener fecha de finalización
        if is_current_job and end_date:
            raise forms.ValidationError("Si es tu trabajo actual, no debes especificar fecha de finalización.")
        
        # Si no es trabajo actual, debe tener fecha de finalización
        if not is_current_job and not end_date:
            raise forms.ValidationError("Si no es tu trabajo actual, debes especificar la fecha de finalización.")
        
        return cleaned_data

# ===== FORMULARIO: ASIGNACIÓN DE EMPRESAS POR STAFF =====
# (Eliminado - ahora se usa el sistema de historial laboral automático)
