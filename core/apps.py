# ===== CONFIGURACIÓN DE LA APLICACIÓN CORE =====
# Este archivo define la configuración específica de la aplicación 'core'
# Django lo usa para identificar y configurar la aplicación

from django.apps import AppConfig

class CoreConfig(AppConfig):
    """
    Configuración de la aplicación 'core' de SelecLoop.
    
    Esta aplicación es el núcleo del sistema y contiene:
    - Modelos de base de datos (empresas, usuarios, reseñas)
    - Vistas y formularios
    - Templates HTML
    - Archivos estáticos (CSS, JS, imágenes)
    - Comandos de gestión personalizados
    """
    
    # ===== CONFIGURACIÓN BÁSICA =====
    default_auto_field = 'django.db.models.BigAutoField'  # Campo de clave primaria por defecto
    name = 'core'  # Nombre de la aplicación (debe coincidir con el directorio)
    
    # ===== CONFIGURACIÓN ADICIONAL =====
    verbose_name = 'Core'  # Nombre legible de la aplicación en el admin
    
    def ready(self):
        """
        Método que se ejecuta cuando la aplicación está lista.
        
        Se usa para:
        - Importar señales (signals)
        - Configuraciones de inicialización
        - Importaciones que requieren que Django esté completamente cargado
        """
        # Importar señales cuando la aplicación esté lista
        # Esto evita problemas de importación circular
        try:
            import core.signals  # noqa
        except ImportError:
            # Las señales no están implementadas aún
            pass
