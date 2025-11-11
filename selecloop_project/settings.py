"""
Configuración del proyecto SelecLoop - Django

Este archivo contiene toda la configuración principal del proyecto Django,
incluyendo aplicaciones instaladas, base de datos, archivos estáticos,
configuración de seguridad y más.

Generado automáticamente por Django 5.2.4
"""

from pathlib import Path

# ===== CONFIGURACIÓN DE RUTAS =====
# Obtiene la ruta base del proyecto (directorio padre de este archivo)
BASE_DIR = Path(__file__).resolve().parent.parent

# ===== CONFIGURACIÓN DE SEGURIDAD =====
# Clave secreta única para el proyecto - NO COMPARTIR EN PRODUCCIÓN
SECRET_KEY = 'django-insecure-dke$qnmk)_*h+g6tr525*-(a*zkd)%ji4t!+gem%%q%bcf_%02'

# Modo de depuración - ACTIVAR SOLO EN DESARROLLO
DEBUG = True

# Hosts permitidos para acceder a la aplicación
ALLOWED_HOSTS = []

# ===== APLICACIONES INSTALADAS =====
INSTALLED_APPS = [
    # Aplicaciones core de Django
    'django.contrib.admin',           # Panel de administración
    'django.contrib.auth',            # Sistema de autenticación
    'django.contrib.contenttypes',    # Sistema de tipos de contenido
    'django.contrib.sessions',        # Sistema de sesiones
    'django.contrib.messages',        # Sistema de mensajes flash
    'django.contrib.staticfiles',     # Gestión de archivos estáticos
    
    # Aplicaciones de terceros
    'crispy_forms',                   # Formularios con mejor presentación
    'crispy_bootstrap5',              # Tema Bootstrap 5 para formularios
    
    # Aplicaciones del proyecto
    'accounts',                       # Gestión de usuarios y autenticación
    'companies',                      # Gestión de empresas
    'reviews',                        # Sistema de reseñas
    'work_history',                   # Historial laboral
    'achievements',                   # Sistema de logros
    'common',                         # Utilidades compartidas
    'core',                           # Aplicación principal del proyecto
]

# ===== CONFIGURACIÓN DE CRISPY FORMS =====
# Permite usar Bootstrap 5 como tema para los formularios
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ===== MIDDLEWARE =====
# Capas de procesamiento que se ejecutan en cada request
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',        # Seguridad básica
    'django.contrib.sessions.middleware.SessionMiddleware', # Gestión de sesiones
    'django.middleware.common.CommonMiddleware',            # Funcionalidad común
    'django.middleware.csrf.CsrfViewMiddleware',            # Protección CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Autenticación
    'django.contrib.messages.middleware.MessageMiddleware', # Mensajes flash
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # Protección clickjacking
]

# ===== CONFIGURACIÓN DE URLS =====
# Archivo principal de URLs del proyecto
ROOT_URLCONF = 'selecloop_project.urls'

# ===== CONFIGURACIÓN DE TEMPLATES =====
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates', # Motor de templates
        'DIRS': [],                    # Directorios adicionales para templates
        'APP_DIRS': True,             # Buscar templates en cada aplicación
        'OPTIONS': {
            'context_processors': [    # Procesadores de contexto automáticos
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.user_badge',  # Badge del usuario
            ],
            'libraries': {
                'common_tags': 'common.templatetags.common_tags',
            },
        },
    },
]

# ===== CONFIGURACIÓN DE WSGI =====
# Punto de entrada para servidores WSGI
WSGI_APPLICATION = 'selecloop_project.wsgi.application'

# ===== CONFIGURACIÓN DE BASE DE DATOS =====
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Motor de base de datos
        'NAME': BASE_DIR / 'db.sqlite3',         # Archivo de base de datos
    }
}

# ===== VALIDACIÓN DE CONTRASEÑAS =====
# Reglas para validar contraseñas de usuarios
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ===== CONFIGURACIÓN INTERNACIONAL =====
# Idioma y zona horaria por defecto
LANGUAGE_CODE = 'en-us'              # Idioma inglés (se puede cambiar a 'es')
TIME_ZONE = 'America/Bogota'             # Zona horaria de Colombia
USE_I18N = True                      # Habilitar internacionalización
USE_TZ = True                        # Habilitar zonas horarias

# ===== CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS =====
# URLs y directorios para CSS, JavaScript, imágenes, etc.
STATIC_URL = 'static/'               # URL base para archivos estáticos
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Directorio donde se recopilan archivos estáticos
STATICFILES_DIRS = [                 # Directorios adicionales para archivos estáticos
    BASE_DIR / 'core' / 'static',    # Archivos estáticos de la app core
]

# ===== CONFIGURACIÓN DE ARCHIVOS DE MEDIA =====
# URLs y directorios para archivos subidos por usuarios
MEDIA_URL = '/media/'                # URL base para archivos de media
MEDIA_ROOT = BASE_DIR / 'media'      # Directorio donde se almacenan archivos de media

# ===== CONFIGURACIÓN ADICIONAL =====
# Campo de clave primaria por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===== CONFIGURACIÓN DE AUTENTICACIÓN =====
# URLs para el sistema de login/logout
LOGIN_URL = 'login'                  # Página de login
LOGIN_REDIRECT_URL = 'dashboard'     # Página después del login exitoso
LOGOUT_REDIRECT_URL = 'login'        # Página después del logout