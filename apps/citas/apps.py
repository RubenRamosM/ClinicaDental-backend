from django.apps import AppConfig


class CitasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.citas'
    verbose_name = 'Gestión de Citas'
    
    def ready(self):
        """Registrar signals cuando la app esté lista"""
        import apps.citas.signals

