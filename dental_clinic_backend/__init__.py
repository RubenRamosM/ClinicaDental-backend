"""
Inicialización del proyecto Django.
Carga Celery para tareas asíncronas.
"""

# Cargar la app de Celery cuando Django inicia
from config.celery import app as celery_app

__all__ = ('celery_app',)
