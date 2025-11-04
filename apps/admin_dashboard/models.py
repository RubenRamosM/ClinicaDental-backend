"""
Modelos para admin_dashboard.
Incluye modelos de inventario como workaround.
"""
# Importar todos los modelos de inventario para que Django los detecte
from .models_inventario import (
    CategoriaInsumo,
    Proveedor,
    Insumo,
    MovimientoInventario,
    AlertaInventario
)

__all__ = [
    'CategoriaInsumo',
    'Proveedor',
    'Insumo',
    'MovimientoInventario',
    'AlertaInventario',
]
