#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para reemplazar caracteres Unicode por ASCII en http_logger.py"""

# Leer el archivo
with open('pruebas_py/http_logger.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazos
replacements = [
    ('📦', '[OBJ]'),
    ('📋', '[ARR]'),
    ('📝', '[STR]'),
    ('🔢', '[NUM]'),
    ('∅', '[NULL]'),
    ('✓', '[BOOL]'),
    ('•', '-'),
    ('└─', '+-'),
    ('📤', '[REQ]'),
    ('📥', '[RESP]'),
    ('ℹ️', '[INFO]'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Escribir el archivo
with open('pruebas_py/http_logger.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Reemplazos completados!")
