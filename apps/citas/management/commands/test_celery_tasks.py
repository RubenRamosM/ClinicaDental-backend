"""
Comando para probar las tareas de Celery manualmente.
Uso: python manage.py test_celery_tasks
"""
from django.core.management.base import BaseCommand
from apps.citas.tasks import enviar_recordatorios_24h, marcar_citas_vencidas
from apps.autenticacion.tasks import limpiar_tokens_expirados


class Command(BaseCommand):
    help = 'Prueba las tareas de Celery configuradas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            choices=['recordatorios', 'vencidas', 'tokens', 'all'],
            default='all',
            help='Tarea específica a ejecutar'
        )

    def handle(self, *args, **options):
        task = options['task']
        
        self.stdout.write(self.style.WARNING('\n🔄 Ejecutando tareas de Celery...\n'))
        
        if task in ['recordatorios', 'all']:
            self.stdout.write(self.style.NOTICE('📧 Ejecutando: enviar_recordatorios_24h'))
            resultado = enviar_recordatorios_24h()
            self.stdout.write(self.style.SUCCESS(f'✅ Resultado: {resultado}\n'))
        
        if task in ['vencidas', 'all']:
            self.stdout.write(self.style.NOTICE('⏰ Ejecutando: marcar_citas_vencidas'))
            resultado = marcar_citas_vencidas()
            self.stdout.write(self.style.SUCCESS(f'✅ Resultado: {resultado}\n'))
        
        if task in ['tokens', 'all']:
            self.stdout.write(self.style.NOTICE('🔐 Ejecutando: limpiar_tokens_expirados'))
            resultado = limpiar_tokens_expirados()
            self.stdout.write(self.style.SUCCESS(f'✅ Resultado: {resultado}\n'))
        
        self.stdout.write(self.style.SUCCESS('✅ Todas las tareas ejecutadas correctamente'))
