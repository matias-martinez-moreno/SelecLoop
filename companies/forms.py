from django import forms
from .models import Company


class CompanyEditForm(forms.ModelForm):
    """Formulario para editar información de empresa"""
    
    class Meta:
        model = Company
        fields = [
            'name',
            'sector', 
            'location',
            'region',
            'country',
            'description',
            'website',
            'logo',
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la empresa'
            }),
            'sector': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sector de la empresa'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad'
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Región/Estado'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'País'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción de la empresa'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Nombre de la Empresa',
            'sector': 'Sector',
            'location': 'Ciudad',
            'region': 'Región/Estado',
            'country': 'País',
            'description': 'Descripción',
            'website': 'Sitio Web',
            'logo': 'Logo',
            'is_active': 'Empresa Activa'
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Solo staff puede cambiar el estado is_active
        if user and not (user.is_staff or (hasattr(user, 'profile') and user.profile.role == 'staff')):
            if 'is_active' in self.fields:
                self.fields['is_active'].widget = forms.HiddenInput()
