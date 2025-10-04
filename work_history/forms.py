# =============================================================================
# FORMULARIOS DE LA APLICACIÓN WORK_HISTORY - SelecLoop
# =============================================================================
# Este archivo define formularios relacionados con historial laboral
#
# Formularios:
# - WorkHistoryForm: Agregar y editar historial laboral del usuario
# =============================================================================

from django import forms
from .models import WorkHistory
from companies.models import Company


# ===== FORMULARIO: HISTORIAL LABORAL =====
class WorkHistoryForm(forms.ModelForm):
    """
    Formulario para agregar y editar historial laboral del usuario.
    Permite a los candidatos agregar empresas donde han trabajado.
    """
    
    # ===== CAMPOS DE RELACIÓN =====
    company_name = forms.CharField(
        max_length=200,
        label="Empresa",
        help_text="Escribe el nombre de la empresa o selecciona una existente",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Google, Microsoft, Empresa Local...',
            'list': 'companies-list'
        })
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
        fields = ['job_title', 'start_date', 'end_date', 'is_current_job']
    
    def __init__(self, *args, **kwargs):
        """Inicialización del formulario"""
        super().__init__(*args, **kwargs)
        
        # Si estamos editando, mostrar el nombre de la empresa actual
        if self.instance and self.instance.pk and self.instance.company:
            self.fields['company_name'].initial = self.instance.company.name
    
    def clean_company_name(self):
        """Validar y obtener/crear la empresa"""
        company_name = self.cleaned_data.get('company_name')
        
        if not company_name:
            raise forms.ValidationError("Debes especificar el nombre de la empresa.")
        
        # Buscar empresa existente
        company, created = Company.objects.get_or_create(
            name=company_name.strip(),
            defaults={
                'description': f'Empresa creada automáticamente: {company_name}',
                'sector': 'No especificado',
                'location': 'No especificada',
                'region': 'No especificada',
                'country': 'Colombia',
                'is_active': True
            }
        )
        
        return company
    
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
    
    def save(self, commit=True):
        """Guardar el formulario con la empresa correcta"""
        instance = super().save(commit=False)
        instance.company = self.cleaned_data['company_name']
        
        if commit:
            instance.save()
        
        return instance
