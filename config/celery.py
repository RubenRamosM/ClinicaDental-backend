"""
Configuración de Celery para tareas asíncronas.
CU17: Recordatorios automáticos
"""
import os
from celery import Celery
from celery.schedules import crontab

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')

# Crear instancia de Celery
app = Celery('dental_clinic_backend')

# Configuración desde settings.py con prefijo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubrir tareas en todas las apps instaladas
app.autodiscover_tasks()

# Configuración de tareas periódicas (Celery Beat)
app.conf.beat_schedule = {
    'enviar-recordatorios-diarios': {
        'task': 'apps.citas.tasks.enviar_recordatorios_24h',
        'schedule': crontab(hour=9, minute=0),  # Ejecutar todos los días a las 9:00 AM
        'options': {
            'description': 'Enviar recordatorios de citas para el día siguiente',
        }
    },
    'verificar-citas-vencidas': {
        'task': 'apps.citas.tasks.marcar_citas_vencidas',
        'schedule': crontab(hour=0, minute=30),  # Ejecutar a las 12:30 AM
        'options': {
            'description': 'Marcar automáticamente citas vencidas que no fueron confirmadas',
        }
    },
    'limpiar-tokens-expirados': {
        'task': 'apps.autenticacion.tasks.limpiar_tokens_expirados',
        'schedule': crontab(hour=3, minute=0),  # Ejecutar a las 3:00 AM
        'options': {
            'description': 'Eliminar tokens de autenticación expirados',
        }
    },
}

# Configuración de zona horaria
app.conf.timezone = 'America/Lima'  # Ajustar según tu zona horaria

# Configuración de resultado de tareas
app.conf.result_backend = 'redis://localhost:6379/0'
app.conf.result_expires = 3600  # Los resultados expiran en 1 hora

# Configuración de serialización
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

# Logging
app.conf.worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
app.conf.worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de prueba para verificar que Celery funciona."""
    print(f'Request: {self.request!r}')
