"""
Test script to verify PagoEnLineaViewSet filtering works correctly.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sistema_pagos.models import PagoEnLinea
from apps.usuarios.models import Usuario
from django.test import RequestFactory
from apps.sistema_pagos.views import PagoEnLineaViewSet

# Get a patient user (ana.lopez)
paciente_user = Usuario.objects.get(correo="ana.lopez@email.com")
print(f"✓ Usuario paciente encontrado: {paciente_user.correo}")
print(f"  - ID: {paciente_user.idusuario}")
print(f"  - Tiene perfil paciente: {hasattr(paciente_user, 'paciente')}")

if hasattr(paciente_user, 'paciente'):
    print(f"  - Paciente ID: {paciente_user.paciente.codusuario_id}")

# Create a mock request
factory = RequestFactory()
request = factory.get('/api/v1/pagos/pagos-online/')
request.user = paciente_user

# Test the viewset's get_queryset method
viewset = PagoEnLineaViewSet()
viewset.request = request

queryset = viewset.get_queryset()
print(f"\n📊 Queryset para {paciente_user.correo}:")
print(f"   Total pagos: {queryset.count()}")

for pago in queryset:
    print(f"\n   - Pago ID {pago.id}:")
    print(f"     Código: {pago.codigo_pago}")
    print(f"     Monto: ${pago.monto} {pago.moneda}")
    print(f"     Estado: {pago.estado}")
    if pago.consulta:
        print(f"     Consulta ID: {pago.consulta.id}")
        print(f"     Paciente: {pago.consulta.codpaciente.codusuario.correo}")

# Also test with admin to see all pagos
admin_user = Usuario.objects.get(correo="admin@clinica.com")
request.user = admin_user
viewset.request = request

queryset_admin = viewset.get_queryset()
print(f"\n📊 Queryset para admin (todos los pagos):")
print(f"   Total pagos: {queryset_admin.count()}")

print("\n✅ Test completado!")
