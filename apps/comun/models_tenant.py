"""
Modelos para Multitenancy - Sistema de Clínicas Dentales
Cada clínica es un tenant con su propio subdominio
"""
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Clinica(TenantMixin):
    """
    Modelo de Tenant - Representa una clínica dental
    Cada clínica tiene su propio subdominio y esquema de BD separado
    
    Ejemplos:
    - clinica1.psicoadmin.xyz
    - clinica2.psicoadmin.xyz
    """
    nombre = models.CharField(max_length=200, help_text="Nombre de la clínica")
    ruc = models.CharField(max_length=20, unique=True, help_text="RUC/NIT de la clínica")
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Información del administrador de la clínica
    admin_nombre = models.CharField(max_length=200, help_text="Nombre del administrador")
    admin_email = models.EmailField(help_text="Email del administrador")
    admin_telefono = models.CharField(max_length=50, blank=True, null=True)
    
    # Estado de la clínica
    activa = models.BooleanField(default=True, help_text="Si la clínica está activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Plan de suscripción (para facturación futura)
    plan = models.CharField(
        max_length=20, 
        choices=[
            ('basico', 'Básico'),
            ('profesional', 'Profesional'),
            ('empresarial', 'Empresarial'),
        ],
        default='basico'
    )
    max_usuarios = models.IntegerField(default=10, help_text="Máximo de usuarios permitidos")
    max_pacientes = models.IntegerField(default=100, help_text="Máximo de pacientes permitidos")
    
    # Logo de la clínica
    logo_url = models.URLField(blank=True, null=True, help_text="URL del logo en S3")
    
    # TenantMixin automáticamente agrega:
    # - schema_name: nombre del esquema en PostgreSQL
    # - auto_create_schema: True
    # - auto_drop_schema: False
    
    class Meta:
        verbose_name = "Clínica"
        verbose_name_plural = "Clínicas"
    
    def __str__(self):
        return f"{self.nombre} ({self.schema_name})"


class Dominio(DomainMixin):
    """
    Modelo de Dominio - Asocia subdominios con clínicas
    
    Ejemplos:
    - psicoadmin.xyz -> tenant público (super admin)
    - clinica1.psicoadmin.xyz -> Clínica 1
    - clinica2.psicoadmin.xyz -> Clínica 2
    """
    class Meta:
        verbose_name = "Dominio"
        verbose_name_plural = "Dominios"
    
    def __str__(self):
        return f"{self.domain} -> {self.tenant.nombre if self.tenant else 'Sin tenant'}"
