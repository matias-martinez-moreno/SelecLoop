# =============================================================================
# FORMULARIOS DE LA APLICACIÓN REVIEWS - SelecLoop
# =============================================================================
# Este archivo define formularios relacionados con reseñas
#
# Formularios:
# - ReviewForm: Creación y edición de reseñas con calificaciones
# =============================================================================

from django import forms
from .models import Review
from companies.models import Company


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
        help_text="Selecciona la empresa donde participaste en el proceso de selección",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
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
    
    # ===== CAMPOS DE CALIFICACIÓN =====
    OVERALL_RATING_CHOICES = [
        (1, '1 - Muy Malo'),
        (2, '2 - Malo'),
        (3, '3 - Regular'),
        (4, '4 - Bueno'),
        (5, '5 - Excelente'),
    ]
    
    overall_rating = forms.ChoiceField(
        choices=OVERALL_RATING_CHOICES,
        label="Calificación general",
        help_text="Califica tu experiencia general del proceso de selección (1 = Muy malo, 5 = Excelente)",
        widget=forms.Select(attrs={
            'class': 'form-control'
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
        if overall_rating:
            try:
                rating_value = int(overall_rating)
                if rating_value < 1 or rating_value > 5:
                    raise forms.ValidationError('La calificación general debe estar entre 1 y 5.')
            except (ValueError, TypeError):
                raise forms.ValidationError('La calificación general debe ser un número válido.')
        
        return cleaned_data
