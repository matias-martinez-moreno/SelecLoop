# ===== CONFIGURACIÓN DE LA APLICACIÓN CORE =====
# Este archivo define la configuración específica de la aplicación 'core'
# Django lo usa para identificar y configurar la aplicación

import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

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
        - Precargar servicios pesados como modelos de ML
        """
        # Importar señales cuando la aplicación esté lista
        # Esto evita problemas de importación circular
        try:
            import core.signals  # noqa
        except ImportError:
            # Las señales no están implementadas aún
            pass
        
        # Precargar el servicio de verificación al iniciar Django
        # Esto carga los modelos de Hugging Face una sola vez al inicio
        # en lugar de cargarlos cada vez que se crea una reseña
        try:
            from core.services.review_verification import ReviewVerificationService, ML_AVAILABLE
            service = ReviewVerificationService()  # Se carga una sola vez aquí (Singleton)
            
            if ML_AVAILABLE:
                if service.models_loaded:
                    logger.info("=" * 60)
                    logger.info("✅ ReviewVerificationService PRECARGADO EXITOSAMENTE")
                    logger.info("✅ Modelos de Hugging Face ACTIVOS y LISTOS")
                    logger.info(f"   - Toxicity model: {'✅ Cargado' if service.toxicity_pipeline else '❌ No disponible'}")
                    logger.info(f"   - Sentiment model: {'✅ Cargado' if service.sentiment_pipeline else '❌ No disponible'}")
                    logger.info("=" * 60)
                else:
                    logger.warning("⚠️ ReviewVerificationService precargado pero los modelos NO se cargaron.")
                    logger.warning("⚠️ Se usarán verificaciones básicas solamente.")
            else:
                logger.warning("⚠️ Librerías ML (torch/transformers) no disponibles.")
                logger.warning("⚠️ Se usarán verificaciones básicas solamente.")
        except Exception as e:
            logger.error(f"❌ Error al precargar ReviewVerificationService: {e}", exc_info=True)
