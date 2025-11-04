#!/usr/bin/env python
"""
Script para corregir campos en archivos .http
Cambia "email" por "correo" y "contraseña" por "password"
"""

import os
import glob

# Directorio de archivos .http
http_dir = "pruebas_http"

# Buscar todos los archivos .http
http_files = glob.glob(os.path.join(http_dir, "*.http"))

print(f"🔍 Encontrados {len(http_files)} archivos .http")

for filepath in http_files:
    print(f"\n📝 Procesando: {os.path.basename(filepath)}")
    
    # Leer contenido
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Contador de cambios
    cambios = 0
    
    # Reemplazar "email": por "correo":
    content_nuevo = content.replace('"email":', '"correo":')
    if content_nuevo != content:
        cambios += content_nuevo.count('"correo":') - content.count('"correo":')
        content = content_nuevo
    
    # Reemplazar "contraseña": por "password":
    content_nuevo = content.replace('"contraseña":', '"password":')
    if content_nuevo != content:
        cambios += content_nuevo.count('"password":') - content.count('"password":')
        content = content_nuevo
    
    # Guardar cambios
    if cambios > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✅ {cambios} cambios aplicados")
    else:
        print(f"   ℹ️  Sin cambios necesarios")

print("\n✨ ¡Corrección completada!")
