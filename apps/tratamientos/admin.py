from django.contrib import admin
from .models import PlanTratamiento, Presupuesto, ItemPresupuesto, Procedimiento


@admin.register(PlanTratamiento)
class PlanTratamientoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'paciente', 'odontologo', 'estado', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['codigo', 'paciente__usuario__nombre', 'descripcion']
    readonly_fields = ['codigo', 'fecha_creacion', 'fecha_aprobacion']


@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'plan_tratamiento', 'total', 'estado', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['codigo']
    readonly_fields = ['codigo', 'total', 'fecha_creacion', 'fecha_aprobacion']


@admin.register(ItemPresupuesto)
class ItemPresupuestoAdmin(admin.ModelAdmin):
    list_display = ['presupuesto', 'servicio', 'cantidad', 'precio_unitario', 'total']
    list_filter = ['presupuesto']
    readonly_fields = ['total']


@admin.register(Procedimiento)
class ProcedimientoAdmin(admin.ModelAdmin):
    list_display = ['servicio', 'plan_tratamiento', 'estado', 'fecha_planificada', 'fecha_realizado']
    list_filter = ['estado', 'fecha_planificada']
    search_fields = ['servicio__nombreservicio', 'descripcion']
    readonly_fields = ['fecha_realizado']
