"""
Comando de Django para crear respaldos manuales desde CLI.

Uso:
    python manage.py crear_respaldo --clinica 1
    python manage.py crear_respaldo --clinica 1 --descripcion "Respaldo antes de actualización"
"""
from django.core.management.base import BaseCommand, CommandError
from respaldos.services import BackupService


class Command(BaseCommand):
    help = 'Crear respaldo manual de datos de una clínica'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clinica',
            type=int,
            required=True,
            help='ID de la clínica a respaldar'
        )
        parser.add_argument(
            '--descripcion',
            type=str,
            default='',
            help='Descripción del respaldo'
        )

    def handle(self, *args, **options):
        clinica_id = options['clinica']
        descripcion = options['descripcion']
        
        self.stdout.write(
            self.style.WARNING(f'Iniciando respaldo para clínica {clinica_id}...')
        )
        
        try:
            backup_service = BackupService()
            respaldo = backup_service.crear_respaldo(
                clinica_id=clinica_id,
                tipo='manual',
                descripcion=descripcion
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Respaldo creado exitosamente!')
            )
            self.stdout.write(f'  ID: {respaldo.id}')
            self.stdout.write(f'  Archivo S3: {respaldo.archivo_s3}')
            self.stdout.write(f'  Tamaño: {respaldo.tamaño_bytes / (1024 * 1024):.2f} MB')
            self.stdout.write(f'  Registros: {respaldo.numero_registros}')
            self.stdout.write(f'  Tiempo: {respaldo.tiempo_ejecucion.total_seconds():.2f}s')
            self.stdout.write(f'  Hash MD5: {respaldo.hash_md5}')
            
            if respaldo.metadata:
                self.stdout.write(f'\n  Detalles de compresión:')
                self.stdout.write(f'    - Original: {respaldo.metadata.get("tamaño_original_mb", 0)} MB')
                self.stdout.write(f'    - Comprimido: {respaldo.metadata.get("tamaño_comprimido_mb", 0)} MB')
                self.stdout.write(f'    - Reducción: {respaldo.metadata.get("compresion_porcentaje", 0)}%')
            
        except Exception as e:
            raise CommandError(f'Error al crear respaldo: {e}')
