# ===== CONFIGURACIÓN DEL PANEL DE ADMINISTRACIÓN =====
# Configuración del admin para los modelos de companies

from django.contrib import admin
from .models import Company

# ===== ADMIN: EMPRESAS =====
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Company.
    Permite gestionar empresas desde el panel de administración.
    """
    
    # ===== CAMPOS MOSTRADOS EN LA LISTA =====
    list_display = [
        'name',           # Nombre de la empresa
        'sector',         # Sector de la empresa
        'location',       # Ubicación de la empresa
        'is_active',      # Estado activo/inactivo
        'created_at'      # Fecha de creación
    ]
    
    # ===== FILTROS DISPONIBLES =====
    list_filter = [
        'sector',         # Filtrar por sector
        'location',       # Filtrar por ubicación
        'is_active',      # Filtrar por estado
        'created_at'      # Filtrar por fecha de creación
    ]
    
    # ===== CAMPOS DE BÚSQUEDA =====
    search_fields = [
        'name',           # Buscar por nombre
        'sector',         # Buscar por sector
        'location'        # Buscar por ubicación
    ]
    
    # ===== CAMPOS EDITABLES EN LA LISTA =====
    list_editable = ['is_active']  # Cambiar estado sin entrar al detalle
    
    # ===== ORDENAMIENTO =====
    ordering = ['name']  # Ordenar alfabéticamente por nombre