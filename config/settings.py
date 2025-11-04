"""
Django settings for config project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

# ... resto de la configuración
# ------------------------------------
# Seguridad / Debug
# ------------------------------------
# IMPORTANTE: Usa variables de entorno en producción
SECRET_KEY = os.environ.get('SECRET_KEY') or os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise Exception("SECRET_KEY o DJANGO_SECRET_KEY no está configurada")

DEBUG = os.environ.get('DEBUG', 'False') == 'True'  # Por defecto False en producción

# ------------------------------------
# Seguridad - Allowed Hosts / CORS / CSRF
# ------------------------------------
# Permitir configuración desde variable de entorno (para Render/producción)
if os.environ.get('ALLOWED_HOSTS'):
    ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS').split(',')]
else:
    # Configuración por defecto para desarrollo
    ALLOWED_HOSTS = [
        "localhost",
        ".dpdns.org",
        "127.0.0.1",
        "3.137.195.59",
        "18.220.214.178",
        "18.224.189.52",
        ".amazonaws.com",
        "ec2-18-220-214-178.us-east-2.compute.amazonaws.com",
        "notificct.dpdns.org",
        "balancearin-1841542738.us-east-2.elb.amazonaws.com",
        ".localhost",
        ".test",  # Para desarrollo local con subdominios
        ".notificct.dpdns.org",
        # Vercel deployment
        "buy-dental-smile.vercel.app",
        # Desarrollo móvil
        "10.0.2.2",  # Emulador Android
        "10.0.3.2",  # Emulador Android (alternativo)
        # Render
        ".onrender.com",
        ".psicoadmin.xyz",
        "psicoadmin.xyz",
        "www.psicoadmin.xyz",
    ]

# En desarrollo, permitir también IPs de red local (192.168.*.*)
if DEBUG:
    import socket
    # Obtener IP local automáticamente
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if local_ip not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(local_ip)
    except:
        pass
    # Permitir rango común de red local
    ALLOWED_HOSTS.extend([
        "192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4", "192.168.1.5",
        "192.168.0.1", "192.168.0.2", "192.168.0.3", "192.168.0.4", "192.168.0.5",
    ])

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://\w+\.dpdns\.org$",  # Permite https://cualquier-subdominio.dpdns.org
    r"^http://[\w-]+\.localhost:\d+$",  # Subdominios locales
    r"^https://[\w-]+\.vercel\.app$",  # Vercel deployments
    r"^http://localhost:\d+$",  # Desarrollo local
    r"^https://[\w-]+\.psicoadmin\.xyz$",  # Subdominios de producción
    r"^https://[\w-]+\.onrender\.com$",  # Render deployments
]

# En desarrollo, permitir todos los orígenes (incluyendo subdominios)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    # En producción, obtener de variable de entorno o usar defaults
    if os.environ.get('CORS_ALLOWED_ORIGINS'):
        CORS_ALLOWED_ORIGINS = [o.strip() for o in os.environ.get('CORS_ALLOWED_ORIGINS').split(',')]
    else:
        CORS_ALLOWED_ORIGINS = [
            "https://psicoadmin.xyz",
            "https://www.psicoadmin.xyz",
            # Los subdominios se manejan por el regex de arriba
            "https://buy-dental-smile.vercel.app",
        ]

CORS_ALLOW_CREDENTIALS = True

# Permitir headers personalizados (especialmente x-tenant-subdomain)
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-tenant-subdomain',  # Header personalizado para multi-tenancy
]

# CSRF Trusted Origins - Permitir configuración desde variable de entorno
if os.environ.get('CSRF_TRUSTED_ORIGINS'):
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS').split(',')]
else:
    CSRF_TRUSTED_ORIGINS = [
        "http://18.220.214.178",
        "https://18.220.214.178",
        "https://ec2-18-220-214-178.us-east-2.compute.amazonaws.com",
        # Multi-tenancy: Permitir subdominios en desarrollo
        "http://localhost:5173",
        "http://*.localhost:5173",
        "http://norte.localhost:5173",
        "http://sur.localhost:5173",
        "http://este.localhost:5173",
        # Multi-tenancy: Permitir subdominios en Django development server
        "http://localhost:8000",
        "http://*.localhost:8000",
        "http://norte.localhost:8000",
        "http://sur.localhost:8000",
        "http://este.localhost:8000",
        # Render/Producción
        "https://psicoadmin.xyz",
        "https://www.psicoadmin.xyz",
        "https://*.psicoadmin.xyz",
        "https://*.onrender.com",
        "https://*.notificct.dpdns.org",
        "https://*.dpdns.org",
        "https://buy-dental-smile.vercel.app",
        "https://*.vercel.app",
    ]

# =================================================================
# MULTITENANCY CON DJANGO-TENANTS
# =================================================================

# APPS COMPARTIDAS (público - para super admin)
SHARED_APPS = [
    'django_tenants',  # ← DEBE SER LA PRIMERA APP
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'apps.comun',  # Contiene el modelo Clinica (Tenant) y Dominio
]

# APPS DE TENANTS (cada clínica)
TENANT_APPS = [
    # Django core apps
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    
    # REST Framework
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_filters',
    
    # Apps específicas de cada clínica
    'apps.usuarios',
    'apps.profesionales',
    'apps.citas',
    'apps.administracion_clinica',
    'apps.sistema_pagos',
    'apps.auditoria',
    'apps.autenticacion',
    'apps.historial_clinico',
    'apps.tratamientos',
    'respaldos',
    'apps.chatbot',
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

# Agregar whitenoise al final (para archivos estáticos)
INSTALLED_APPS.append("whitenoise.runserver_nostatic")

# Configuración de Tenant
TENANT_MODEL = "comun.Clinica"
TENANT_DOMAIN_MODEL = "comun.Dominio"

# Database router para tenants
DATABASE_ROUTERS = [
    'django_tenants.routers.TenantSyncRouter',
]

# ------------------------------------
# Middleware
# ------------------------------------
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',  # ← PRIMERO (detecta tenant)
    'apps.comun.middleware.TenantURLRoutingMiddleware',  # ← SEGUNDO (cambia URLs según tenant)
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    
    # Auditoría automática
    "apps.auditoria.middleware.AuditoriaMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                'django_tenants.context_processors.current_tenant',  # ← MULTITENANCY
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ------------------------------------
# Base de datos (Configuración simplificada para Render + Supabase)
# ------------------------------------

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_BACKUP_BUCKET_NAME = os.environ.get('AWS_BACKUP_BUCKET_NAME', 'clinica-dental-backups-2025-bolivia')
AWS_S3_SIGNATURE_NAME = 's3v4',
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_VERITY = True
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# ------------------------------------
# Base de datos (PostgreSQL)
# ------------------------------------
# Configuración de Base de Datos
# ------------------------------------
import dj_database_url

# Construir DATABASE_URL desde variables individuales si no existe
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    # Construir desde variables individuales (desarrollo local)
    db_name = os.environ.get('DB_NAME', 'clinica_dental_dev')
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '5432')
    DATABASE_URL = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

# Parsear DATABASE_URL
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
}

# Asegurar que use el backend de django-tenants
DATABASES['default']['ENGINE'] = 'django_tenants.postgresql_backend'

# ------------------------------------
# Password validators
# ------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------
# Localización
# ------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/La_Paz"
USE_I18N = True
USE_TZ = True

# ------------------------------------
# Archivos estáticos (WhiteNoise)
# ------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = "/media/"  # Corregido: era MEDIA_URLS
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ------------------------------------
# Configuración de Upload de Archivos
# ------------------------------------
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Tipos de archivo permitidos para evidencias
ALLOWED_UPLOAD_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf']
ALLOWED_UPLOAD_MIMETYPES = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'application/pdf'
]

# ------------------------------------
# DRF - CORREGIDO
# ------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    'DEFAULT_THROTTLE_RATES': {
        'notifications': '100/hour',
        'device_registration': '10/day',
        'preference_updates': '50/hour',
        # SP3-T003: Throttling para presupuestos digitales
        'aceptacion_presupuesto': '10/hour',  # Limitar aceptaciones
        'presupuesto_list': '100/hour',  # Limitar consultas de lista
        'presupuesto_anon': '20/day',  # Usuarios anónimos más restrictivo
    }
}

# ------------------------------------
# Otros
# ------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------
# Frontend y Email (para recuperar contraseña)
# ------------------------------------
FRONTEND_URL = "https://buy-dental-smile.vercel.app"
DEFAULT_FROM_EMAIL = "no-reply@clinica.local"

# ------------------------------------
# SaaS Multi-Tenant Configuration
# ------------------------------------
# Dominio base para tenants (sin http:// ni https://)
# En DESARROLLO: localhost
# En PRODUCCIÓN: tu-dominio.com
SAAS_BASE_DOMAIN = "localhost" if DEBUG else "clinicadental.com"
SAAS_PORT = ":8000" if DEBUG else ""

# URL del sitio público (landing page de ventas)
# Este es el dominio SIN subdominio donde los clientes se registran
SAAS_PUBLIC_URL = f"http://{SAAS_BASE_DOMAIN}{SAAS_PORT}" if DEBUG else f"https://{SAAS_BASE_DOMAIN}"

# Ejemplo de URLs resultantes en DESARROLLO:
# - Sitio público: http://localhost:8000
# - Tenant "norte": http://norte.localhost:8000
# - Tenant "sur": http://sur.localhost:8000
# - Tenant "este": http://este.localhost:8000
# - Tenant "oeste": http://oeste.localhost:8000

# Ejemplo de URLs resultantes en PRODUCCIÓN:
# - Sitio público: https://clinicadental.com
# - Tenant "norte": https://norte.clinicadental.com
# - Tenant "sur": https://sur.clinicadental.com
# - Tenant "este": https://este.clinicadental.com
# - Tenant "oeste": https://oeste.clinicadental.com

# ------------------------------------
# Configuración de Email (SMTP)
# ------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.resend.com"  # Cambia esto por tu proveedor de email
EMAIL_PORT = 587
EMAIL_HOST_USER = "apikey"  # Usuario de tu servicio de email
EMAIL_HOST_PASSWORD = ""  # IMPORTANTE: Agrega aquí tu API key de email
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

# ------------------------------------
# CONFIGURACIÓN DE NOTIFICACIONES
# ------------------------------------

# Push Notifications (OneSignal - Opcional)
ONESIGNAL_APP_ID = ""  # Agrega tu OneSignal App ID aquí
ONESIGNAL_REST_API_KEY = ""  # Agrega tu OneSignal REST API Key aquí

# ------------------------------------
# Stripe (Pagos en Línea)
# ------------------------------------
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Configuración de Stripe para pagos de tratamientos (SP3-T009)
STRIPE_ENABLED = bool(STRIPE_SECRET_KEY)  # Solo habilitar si hay SECRET_KEY
STRIPE_DEFAULT_CURRENCY = os.environ.get('STRIPE_CURRENCY', 'BOB')  # Bolivianos
STRIPE_PAYMENT_METHOD_TYPES = ['card']  # Métodos de pago aceptados
STRIPE_CAPTURE_METHOD = 'automatic'  # automatic o manual

# Configuración legacy para SaaS (opcional)
STRIPE_PRICE_ID = os.environ.get('STRIPE_PRICE_ID')
STRIPE_PRICE_AMOUNT = 99  # Precio en USD del plan mensual (solo para mostrar al usuario)

# Advertencia si Stripe no está configurado (no es error fatal)
if not STRIPE_ENABLED:
    import warnings
    warnings.warn("Stripe no está configurado. Los pagos en línea estarán deshabilitados.", UserWarning)

# ------------------------------------
# OpenAI Configuration (Chatbot)
# ------------------------------------
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
OPENAI_ASSISTANT_ID = os.environ.get('OPENAI_ASSISTANT_ID', '')

# Configuración del asistente (se puede ajustar según necesidades)
OPENAI_ASSISTANT_NAME = "Asistente Dental"
OPENAI_ASSISTANT_INSTRUCTIONS = """
Eres un asistente virtual de una clínica dental. Tu función es:
1. Recopilar información sobre síntomas dentales del paciente
2. Evaluar el nivel de urgencia (alta, media, baja)
3. Ayudar a agendar citas cuando el paciente lo solicite
4. Proporcionar información general sobre cuidado dental

Debes ser empático, profesional y claro. Siempre recuerda que NO eres un dentista 
y NO puedes dar diagnósticos médicos, solo orientar y ayudar con el agendamiento.
"""

# Configuración de notificaciones por email
DEFAULT_REMINDER_HOURS = 24
MAX_NOTIFICATION_RETRIES = 3
NOTIFICATION_RETRY_DELAY = 30

# Información de la clínica para emails
CLINIC_INFO = {
    'name': "Clínica Dental",
    'address': "Santa Cruz, Bolivia",
    'phone': "+591 XXXXXXXX",
    'email': "info@clinica.com",
    'website': FRONTEND_URL,
}

# Configuración de logging para notificaciones
import os

logs_dir = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Throttling para APIs de notificaciones
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_RATES': {
        'notifications': '100/hour',
        'device_registration': '10/day',
        'preference_updates': '50/hour',
    }
})
# Al final de settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',  # Cambiado de WARNING a INFO para ver más logs
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',  # DEBUG para máximo detalle
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',  # DEBUG para ver todas las peticiones
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'DEBUG',  # DEBUG para ver peticiones HTTP detalladas
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',  # DEBUG para ver queries SQL
            'propagate': False,
        },
        'api': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Logs de tu app
            'propagate': False,
        },
    },
}

# ------------------------------------
# Configuraciones de Seguridad para Producción
# ------------------------------------
if not DEBUG:
    # HTTPS/SSL Settings
    # IMPORTANTE: SECURE_SSL_REDIRECT deshabilitado para permitir health checks HTTP desde ALB
    # El Load Balancer maneja HTTPS, pero hace health checks por HTTP
    SECURE_SSL_REDIRECT = False  # Cambio: Deshabilitado para health checks
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Security Headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
