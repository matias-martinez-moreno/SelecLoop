# =============================================================================
# TEMPLATE TAGS COMUNES - SelecLoop
# =============================================================================
# Este archivo contiene template tags personalizados comunes para el proyecto
# =============================================================================

from django import template
from datetime import datetime, date

register = template.Library()

# Mapeo de meses en español
MESES_ESPANOL = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

MESES_ESPANOL_CORTO = {
    1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr',
    5: 'may', 6: 'jun', 7: 'jul', 8: 'ago',
    9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
}


@register.filter
def fecha_espanol(fecha, formato='F Y'):
    """
    Formatea una fecha en español.
    
    Uso:
        {{ fecha|fecha_espanol }}  # "enero 2024"
        {{ fecha|fecha_espanol:"M Y" }}  # "ene 2024"
    """
    if not fecha:
        return ''
    
    # Manejar diferentes tipos de fecha (date, datetime, string)
    try:
        # Si es un string, intentar parsearlo
        if isinstance(fecha, str):
            try:
                fecha = datetime.strptime(fecha, '%Y-%m-%d')
            except (ValueError, TypeError):
                try:
                    fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    return fecha
        
        # Obtener mes y año del objeto fecha (date o datetime)
        # Ambos tipos tienen los atributos month y year
        month_num = fecha.month
        year = fecha.year
        
        # Determinar formato (corto o largo)
        usar_corto = 'M' in formato
        
        # Obtener nombre del mes en español
        if usar_corto:
            month_name = MESES_ESPANOL_CORTO.get(month_num, '')
        else:
            month_name = MESES_ESPANOL.get(month_num, '')
        
        # Si no se encuentra el mes en el mapeo, usar fallback
        if not month_name:
            try:
                if hasattr(fecha, 'strftime'):
                    month_name = fecha.strftime('%b' if usar_corto else '%B')
                    # Si el sistema no tiene locale español, el mes puede estar en inglés
                    # En ese caso, intentar traducir manualmente
                    meses_en_ing = {
                        'January': 'enero', 'February': 'febrero', 'March': 'marzo',
                        'April': 'abril', 'May': 'mayo', 'June': 'junio',
                        'July': 'julio', 'August': 'agosto', 'September': 'septiembre',
                        'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
                    }
                    meses_en_ing_corto = {
                        'Jan': 'ene', 'Feb': 'feb', 'Mar': 'mar', 'Apr': 'abr',
                        'May': 'may', 'Jun': 'jun', 'Jul': 'jul', 'Aug': 'ago',
                        'Sep': 'sep', 'Oct': 'oct', 'Nov': 'nov', 'Dec': 'dic'
                    }
                    if usar_corto:
                        month_name = meses_en_ing_corto.get(month_name, month_name)
                    else:
                        month_name = meses_en_ing.get(month_name, month_name)
            except:
                return str(fecha)
        
        # Capitalizar y retornar
        return f"{month_name.capitalize()} {year}"
    except (AttributeError, ValueError, TypeError) as e:
        # Si hay algún error, devolver la representación original
        return str(fecha)

