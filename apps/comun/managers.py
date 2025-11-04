"""
Managers personalizados para QuerySets optimizados.
"""
from django.db import models


class QuerySetActivos(models.QuerySet):
    """
    QuerySet que filtra solo registros activos.
    """
    
    def activos(self):
        """Retorna solo registros activos."""
        return self.filter(activo=True)
    
    def inactivos(self):
        """Retorna solo registros inactivos."""
        return self.filter(activo=False)


class ManagerActivos(models.Manager):
    """
    Manager que por defecto retorna solo registros activos.
    """
    
    def get_queryset(self):
        return QuerySetActivos(self.model, using=self._db).activos()
    
    def inactivos(self):
        """Acceder a registros inactivos."""
        return QuerySetActivos(self.model, using=self._db).inactivos()
    
    def todos(self):
        """Acceder a todos los registros (activos e inactivos)."""
        return QuerySetActivos(self.model, using=self._db)


# TODO (Multi-clínica): Manager para filtrar por clínica
# class QuerySetMultiClinica(models.QuerySet):
#     """
#     QuerySet que filtra automáticamente por clínica.
#     """
#     
#     def para_clinica(self, clinica):
#         """Filtrar por clínica específica."""
#         if clinica is None:
#             return self  # Superadmin ve todo
#         return self.filter(clinica=clinica)
#     
#     def clinica_actual(self):
#         """Filtrar por clínica del request actual."""
#         from threading import local
#         _thread_locals = local()
#         clinica = getattr(_thread_locals, 'clinica', None)
#         return self.para_clinica(clinica)
#
#
# class ManagerMultiClinica(models.Manager):
#     """
#     Manager que aplica filtros de clínica automáticamente.
#     """
#     
#     def get_queryset(self):
#         return QuerySetMultiClinica(self.model, using=self._db)
#     
#     def para_clinica(self, clinica):
#         return self.get_queryset().para_clinica(clinica)
