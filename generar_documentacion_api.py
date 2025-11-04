"""
Script para generar documentación completa de la API
Documenta todos los endpoints con sus estructuras de respuesta
"""
import os
import django
import json
from collections import OrderedDict

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from rest_framework import serializers
from django.urls import get_resolver
from rest_framework.routers import DefaultRouter
import importlib
import inspect

def get_serializer_fields(serializer_class):
    """Extrae los campos de un serializer y sus tipos"""
    try:
        serializer = serializer_class()
        fields_info = OrderedDict()
        
        for field_name, field in serializer.fields.items():
            field_type = field.__class__.__name__
            
            # Determinar el tipo TypeScript
            if isinstance(field, serializers.IntegerField):
                ts_type = "number"
            elif isinstance(field, serializers.FloatField) or isinstance(field, serializers.DecimalField):
                ts_type = "number"
            elif isinstance(field, serializers.BooleanField):
                ts_type = "boolean"
            elif isinstance(field, serializers.DateTimeField):
                ts_type = "string"  # ISO date string
            elif isinstance(field, serializers.DateField):
                ts_type = "string"
            elif isinstance(field, serializers.ListSerializer) or isinstance(field, serializers.ManyRelatedField):
                ts_type = "any[]"
            elif isinstance(field, serializers.DictField) or isinstance(field, serializers.JSONField):
                ts_type = "Record<string, any>"
            elif isinstance(field, serializers.SerializerMethodField):
                ts_type = "any"
            else:
                ts_type = "string"
            
            fields_info[field_name] = {
                'type': field_type,
                'ts_type': ts_type,
                'required': field.required if hasattr(field, 'required') else False,
                'read_only': field.read_only if hasattr(field, 'read_only') else False,
                'help_text': str(field.help_text) if hasattr(field, 'help_text') and field.help_text else ""
            }
        
        return fields_info
    except Exception as e:
        return {"error": str(e)}

def generate_typescript_interface(serializer_name, fields_info):
    """Genera una interfaz TypeScript desde los campos del serializer"""
    interface_name = serializer_name.replace('Serializer', '')
    lines = [f"export interface {interface_name} {{"]
    
    for field_name, field_data in fields_info.items():
        optional = "" if field_data['required'] else "?"
        lines.append(f"  {field_name}{optional}: {field_data['ts_type']};")
    
    lines.append("}")
    return "\n".join(lines)

def document_viewsets():
    """Documenta todos los ViewSets de la aplicación"""
    documentation = []
    
    apps_to_check = [
        'apps.usuarios',
        'apps.tratamientos',
        'apps.profesionales',
        'apps.citas',
        'apps.historial_clinico',
        'apps.sistema_pagos',
        'apps.inventario',
        'apps.administracion_clinica',
        'apps.auditoria',
        'apps.autenticacion',
        'apps.respaldos'
    ]
    
    for app_name in apps_to_check:
        try:
            views_module = importlib.import_module(f'{app_name}.views')
            
            for name, obj in inspect.getmembers(views_module):
                if inspect.isclass(obj) and 'ViewSet' in name:
                    doc_entry = {
                        'viewset': name,
                        'app': app_name,
                        'serializer': None,
                        'fields': None,
                        'typescript_interface': None,
                        'endpoints': []
                    }
                    
                    # Obtener serializer
                    if hasattr(obj, 'serializer_class'):
                        serializer_class = obj.serializer_class
                        doc_entry['serializer'] = serializer_class.__name__
                        
                        # Extraer campos
                        fields_info = get_serializer_fields(serializer_class)
                        doc_entry['fields'] = fields_info
                        
                        # Generar interfaz TypeScript
                        if 'error' not in fields_info:
                            doc_entry['typescript_interface'] = generate_typescript_interface(
                                serializer_class.__name__, 
                                fields_info
                            )
                    
                    # Detectar custom actions
                    for method_name in dir(obj):
                        method = getattr(obj, method_name)
                        if hasattr(method, 'mapping'):
                            doc_entry['endpoints'].append({
                                'action': method_name,
                                'methods': list(method.mapping.keys()) if hasattr(method, 'mapping') else [],
                                'detail': getattr(method, 'detail', False)
                            })
                    
                    documentation.append(doc_entry)
        
        except (ImportError, AttributeError) as e:
            print(f"⚠️ No se pudo cargar {app_name}: {e}")
    
    return documentation

def generate_markdown_documentation(documentation):
    """Genera documentación en formato Markdown"""
    md_lines = [
        "# 📚 Documentación Completa de la API",
        "",
        f"**Generado:** {django.utils.timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        ""
    ]
    
    for doc in documentation:
        md_lines.extend([
            f"## 🔷 {doc['viewset']}",
            "",
            f"**App:** `{doc['app']}`  ",
            f"**Serializer:** `{doc['serializer']}`",
            ""
        ])
        
        if doc['typescript_interface']:
            md_lines.extend([
                "### TypeScript Interface",
                "",
                "```typescript",
                doc['typescript_interface'],
                "```",
                ""
            ])
        
        if doc['fields'] and 'error' not in doc['fields']:
            md_lines.extend([
                "### Campos",
                "",
                "| Campo | Tipo Python | Tipo TypeScript | Requerido | Solo Lectura |",
                "|-------|-------------|-----------------|-----------|--------------|"
            ])
            
            for field_name, field_data in doc['fields'].items():
                required = "✅" if field_data['required'] else "❌"
                readonly = "✅" if field_data['read_only'] else "❌"
                md_lines.append(
                    f"| `{field_name}` | {field_data['type']} | `{field_data['ts_type']}` | {required} | {readonly} |"
                )
            
            md_lines.append("")
        
        if doc['endpoints']:
            md_lines.extend([
                "### Endpoints Custom",
                ""
            ])
            for endpoint in doc['endpoints']:
                methods = ', '.join(endpoint['methods']).upper()
                detail = "Detail" if endpoint['detail'] else "List"
                md_lines.append(f"- **{endpoint['action']}** - `{methods}` - {detail}")
            md_lines.append("")
        
        md_lines.append("---")
        md_lines.append("")
    
    return "\n".join(md_lines)

def generate_typescript_file(documentation):
    """Genera un archivo .ts con todas las interfaces"""
    ts_lines = [
        "/**",
        " * Interfaces TypeScript generadas automáticamente desde Django REST Framework",
        f" * Generado: {django.utils.timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
        " * ⚠️ NO EDITAR MANUALMENTE - Regenerar con generar_documentacion_api.py",
        " */",
        ""
    ]
    
    for doc in documentation:
        if doc['typescript_interface']:
            ts_lines.extend([
                f"// {doc['viewset']} - {doc['app']}",
                doc['typescript_interface'],
                ""
            ])
    
    return "\n".join(ts_lines)

if __name__ == "__main__":
    print("🔍 Analizando ViewSets y Serializers...")
    
    documentation = document_viewsets()
    
    print(f"\n✅ Encontrados {len(documentation)} ViewSets")
    
    # Generar Markdown
    md_content = generate_markdown_documentation(documentation)
    with open('API_DOCUMENTATION.md', 'w', encoding='utf-8') as f:
        f.write(md_content)
    print("📄 Generado: API_DOCUMENTATION.md")
    
    # Generar TypeScript
    ts_content = generate_typescript_file(documentation)
    with open('api-types.ts', 'w', encoding='utf-8') as f:
        f.write(ts_content)
    print("📘 Generado: api-types.ts")
    
    # Generar JSON para procesamiento adicional
    json_data = []
    for doc in documentation:
        json_data.append({
            'viewset': doc['viewset'],
            'app': doc['app'],
            'serializer': doc['serializer'],
            'fields': doc['fields']
        })
    
    with open('api-schema.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print("📊 Generado: api-schema.json")
    
    print("\n✨ ¡Documentación generada exitosamente!")
    print("\n📂 Archivos creados:")
    print("   - API_DOCUMENTATION.md  (Documentación legible)")
    print("   - api-types.ts          (Interfaces TypeScript)")
    print("   - api-schema.json       (Esquema JSON)")
