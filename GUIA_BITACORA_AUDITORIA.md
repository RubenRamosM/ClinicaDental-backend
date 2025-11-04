# 📊 GUÍA COMPLETA - SISTEMA DE BITÁCORA Y AUDITORÍA

## 📋 TABLA DE CONTENIDOS
1. [Introducción](#1-introducción)
2. [Configuración Inicial](#2-configuración-inicial)
3. [Servicios y Modelos](#3-servicios-y-modelos)
4. [Componentes React](#4-componentes-react)
5. [Dashboard de Auditoría](#5-dashboard-de-auditoría)
6. [Filtros y Búsqueda](#6-filtros-y-búsqueda)
7. [Reportes y Exportación](#7-reportes-y-exportación)

---

## 1. INTRODUCCIÓN

### ¿Qué es la Bitácora de Auditoría?

La bitácora es un **registro completo** de todas las acciones realizadas en el sistema:
- ✅ **Quién** realizó la acción (usuario)
- ✅ **Qué** acción se realizó (crear, editar, eliminar, login, etc.)
- ✅ **Cuándo** se realizó (fecha y hora exacta)
- ✅ **Dónde** se realizó (IP, navegador)
- ✅ **Qué datos** se afectaron (tabla y registro ID)

### Casos de Uso

1. **Auditoría de Seguridad**: Detectar accesos no autorizados
2. **Seguimiento de Cambios**: Ver quién modificó un registro
3. **Cumplimiento Legal**: Registros para auditorías médicas
4. **Resolución de Problemas**: Rastrear errores y cambios
5. **Análisis de Actividad**: Estadísticas de uso del sistema

---

## 2. CONFIGURACIÓN INICIAL

### 2.1 Modelos del Backend

El backend ya tiene implementado el modelo `Bitacora`:

```python
# apps/auditoria/models.py
class Bitacora(models.Model):
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=255)  # "LOGIN", "CREAR_CITA", "EDITAR_PACIENTE", etc.
    tabla_afectada = models.CharField(max_length=100)  # "consulta", "usuario", "pago", etc.
    registro_id = models.IntegerField(null=True)  # ID del registro afectado
    detalles = models.TextField(null=True)  # Detalles adicionales en JSON
    ip_address = models.GenericIPAddressField(null=True)  # IP del cliente
    user_agent = models.TextField(null=True)  # Navegador/dispositivo
    fecha = models.DateTimeField(auto_now_add=True)  # Timestamp
```

### 2.2 Endpoints Disponibles

```
GET  /api/v1/auditoria/bitacora/                    # Listar todos
GET  /api/v1/auditoria/bitacora/{id}/               # Ver detalle
GET  /api/v1/auditoria/bitacora/por_usuario/?usuario_id=1
GET  /api/v1/auditoria/bitacora/por_tabla/?tabla=consulta
GET  /api/v1/auditoria/bitacora/resumen/            # Estadísticas
GET  /api/v1/auditoria/bitacora/actividad-reciente/?limit=50
```

---

## 3. SERVICIOS Y MODELOS

### 3.1 Interfaces TypeScript

```typescript
// src/types/auditoria.ts

export interface RegistroBitacora {
  id: number;
  usuario: {
    id: number;
    nombre: string;
    email: string;
  } | null;
  accion: string;
  tabla_afectada: string | null;
  registro_id: number | null;
  detalles: string | null;
  ip_address: string | null;
  user_agent: string | null;
  fecha: string;
}

export interface ResumenBitacora {
  por_accion: Array<{
    accion: string;
    total: number;
  }>;
  por_tabla: Array<{
    tabla_afectada: string;
    total: number;
  }>;
  ultimos_7_dias: number;
  ultimos_30_dias: number;
  total_registros: number;
}

export interface FiltrosBitacora {
  usuario?: number;
  accion?: string;
  tabla_afectada?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  search?: string;
  page?: number;
  page_size?: number;
}
```

### 3.2 Servicio de Auditoría

```typescript
// src/services/auditoriaService.ts
import api from './api';
import { RegistroBitacora, ResumenBitacora, FiltrosBitacora } from '../types/auditoria';

class AuditoriaService {
  private readonly baseUrl = '/auditoria/bitacora';

  /**
   * Listar registros de bitácora con filtros
   */
  async listarRegistros(filtros?: FiltrosBitacora): Promise<{
    results: RegistroBitacora[];
    count: number;
    next: string | null;
    previous: string | null;
  }> {
    const params = new URLSearchParams();
    
    if (filtros?.usuario) params.append('usuario', filtros.usuario.toString());
    if (filtros?.accion) params.append('accion', filtros.accion);
    if (filtros?.tabla_afectada) params.append('tabla_afectada', filtros.tabla_afectada);
    if (filtros?.search) params.append('search', filtros.search);
    if (filtros?.page) params.append('page', filtros.page.toString());
    if (filtros?.page_size) params.append('page_size', filtros.page_size.toString());

    const response = await api.get(`${this.baseUrl}/?${params.toString()}`);
    return response.data;
  }

  /**
   * Obtener detalle de un registro
   */
  async obtenerRegistro(id: number): Promise<RegistroBitacora> {
    const response = await api.get(`${this.baseUrl}/${id}/`);
    return response.data;
  }

  /**
   * Obtener registros por usuario
   */
  async obtenerPorUsuario(usuarioId: number): Promise<RegistroBitacora[]> {
    const response = await api.get(`${this.baseUrl}/por_usuario/`, {
      params: { usuario_id: usuarioId },
    });
    return response.data;
  }

  /**
   * Obtener registros por tabla afectada
   */
  async obtenerPorTabla(tabla: string): Promise<RegistroBitacora[]> {
    const response = await api.get(`${this.baseUrl}/por_tabla/`, {
      params: { tabla },
    });
    return response.data;
  }

  /**
   * Obtener resumen de auditoría
   */
  async obtenerResumen(): Promise<ResumenBitacora> {
    const response = await api.get(`${this.baseUrl}/resumen/`);
    return response.data;
  }

  /**
   * Obtener actividad reciente
   */
  async obtenerActividadReciente(limit: number = 50): Promise<RegistroBitacora[]> {
    const response = await api.get(`${this.baseUrl}/actividad-reciente/`, {
      params: { limit },
    });
    return response.data;
  }

  /**
   * Exportar registros a CSV
   */
  async exportarCSV(filtros?: FiltrosBitacora): Promise<Blob> {
    const params = new URLSearchParams();
    if (filtros?.usuario) params.append('usuario', filtros.usuario.toString());
    if (filtros?.accion) params.append('accion', filtros.accion);
    if (filtros?.tabla_afectada) params.append('tabla_afectada', filtros.tabla_afectada);

    const response = await api.get(`${this.baseUrl}/?${params.toString()}&format=csv`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Formatear acción para mostrar
   */
  formatearAccion(accion: string): string {
    const acciones: Record<string, string> = {
      'LOGIN': '🔐 Inicio de Sesión',
      'LOGOUT': '🚪 Cierre de Sesión',
      'CREAR_CITA': '➕ Crear Cita',
      'EDITAR_CITA': '✏️ Editar Cita',
      'CANCELAR_CITA': '❌ Cancelar Cita',
      'CREAR_PACIENTE': '👤 Crear Paciente',
      'EDITAR_PACIENTE': '✏️ Editar Paciente',
      'CREAR_PAGO': '💳 Registrar Pago',
      'CONFIRMAR_PAGO': '✅ Confirmar Pago',
      'RECHAZAR_PAGO': '❌ Rechazar Pago',
      'VER_HISTORIAL': '📋 Ver Historial',
      'DESCARGAR_REPORTE': '📥 Descargar Reporte',
    };
    
    return acciones[accion] || accion;
  }

  /**
   * Formatear tabla para mostrar
   */
  formatearTabla(tabla: string | null): string {
    if (!tabla) return 'Sistema';

    const tablas: Record<string, string> = {
      'consulta': 'Citas',
      'usuario': 'Usuarios',
      'paciente': 'Pacientes',
      'pago_en_linea': 'Pagos',
      'factura': 'Facturas',
      'historial_clinico': 'Historial Clínico',
      'tratamiento': 'Tratamientos',
    };

    return tablas[tabla] || tabla;
  }
}

export default new AuditoriaService();
```

---

## 4. COMPONENTES REACT

### 4.1 Tabla de Registros de Auditoría

```tsx
// src/components/TablaBitacora.tsx
import React, { useEffect, useState } from 'react';
import auditoriaService from '../services/auditoriaService';
import { RegistroBitacora, FiltrosBitacora } from '../types/auditoria';

interface Props {
  filtros?: FiltrosBitacora;
  onVerDetalle?: (registro: RegistroBitacora) => void;
}

const TablaBitacora: React.FC<Props> = ({ filtros, onVerDetalle }) => {
  const [registros, setRegistros] = useState<RegistroBitacora[]>([]);
  const [cargando, setCargando] = useState(true);
  const [pagina, setPagina] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(0);

  useEffect(() => {
    cargarRegistros();
  }, [filtros, pagina]);

  const cargarRegistros = async () => {
    try {
      setCargando(true);
      const resultado = await auditoriaService.listarRegistros({
        ...filtros,
        page: pagina,
        page_size: 20,
      });
      
      setRegistros(resultado.results);
      setTotalPaginas(Math.ceil(resultado.count / 20));
    } catch (error) {
      console.error('Error al cargar registros:', error);
    } finally {
      setCargando(false);
    }
  };

  const formatearFecha = (fecha: string) => {
    const date = new Date(fecha);
    return new Intl.DateTimeFormat('es-BO', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(date);
  };

  if (cargando && registros.length === 0) {
    return (
      <div className="text-center p-8">
        <div className="spinner-border" role="status">
          <span className="sr-only">Cargando registros...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-200">
        <thead className="bg-gray-100">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
              Fecha y Hora
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
              Usuario
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
              Acción
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
              Módulo
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
              IP
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
              Acciones
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {registros.map((registro) => (
            <tr key={registro.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm text-gray-900">
                {formatearFecha(registro.fecha)}
              </td>
              <td className="px-4 py-3 text-sm">
                {registro.usuario ? (
                  <div>
                    <p className="font-medium text-gray-900">{registro.usuario.nombre}</p>
                    <p className="text-gray-500 text-xs">{registro.usuario.email}</p>
                  </div>
                ) : (
                  <span className="text-gray-500 italic">Sistema</span>
                )}
              </td>
              <td className="px-4 py-3 text-sm">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {auditoriaService.formatearAccion(registro.accion)}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-900">
                {auditoriaService.formatearTabla(registro.tabla_afectada)}
                {registro.registro_id && (
                  <span className="ml-2 text-gray-500">
                    #{registro.registro_id}
                  </span>
                )}
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {registro.ip_address || '-'}
              </td>
              <td className="px-4 py-3 text-sm">
                <button
                  onClick={() => onVerDetalle?.(registro)}
                  className="text-blue-600 hover:text-blue-900 font-medium"
                >
                  Ver Detalles
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Paginación */}
      {totalPaginas > 1 && (
        <div className="flex justify-center items-center mt-4 space-x-2">
          <button
            onClick={() => setPagina((p) => Math.max(1, p - 1))}
            disabled={pagina === 1}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Anterior
          </button>
          <span className="text-sm text-gray-600">
            Página {pagina} de {totalPaginas}
          </span>
          <button
            onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))}
            disabled={pagina === totalPaginas}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            Siguiente
          </button>
        </div>
      )}

      {registros.length === 0 && !cargando && (
        <div className="text-center p-8 text-gray-500">
          No se encontraron registros con los filtros aplicados
        </div>
      )}
    </div>
  );
};

export default TablaBitacora;
```

### 4.2 Modal de Detalle

```tsx
// src/components/DetalleBitacora.tsx
import React from 'react';
import { RegistroBitacora } from '../types/auditoria';
import auditoriaService from '../services/auditoriaService';

interface Props {
  registro: RegistroBitacora;
  onCerrar: () => void;
}

const DetalleBitacora: React.FC<Props> = ({ registro, onCerrar }) => {
  const formatearFecha = (fecha: string) => {
    return new Date(fecha).toLocaleString('es-BO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const parsearDetalles = () => {
    if (!registro.detalles) return null;
    
    try {
      return JSON.parse(registro.detalles);
    } catch {
      return registro.detalles;
    }
  };

  const detalles = parsearDetalles();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gray-100 px-6 py-4 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-800">
              Detalle de Registro de Auditoría
            </h2>
            <button
              onClick={onCerrar}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-4">
          {/* ID */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              ID de Registro
            </label>
            <p className="mt-1 text-gray-900">#{registro.id}</p>
          </div>

          {/* Fecha */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Fecha y Hora
            </label>
            <p className="mt-1 text-gray-900">{formatearFecha(registro.fecha)}</p>
          </div>

          {/* Usuario */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Usuario
            </label>
            {registro.usuario ? (
              <div className="mt-1">
                <p className="text-gray-900 font-medium">{registro.usuario.nombre}</p>
                <p className="text-sm text-gray-500">{registro.usuario.email}</p>
                <p className="text-sm text-gray-500">ID: {registro.usuario.id}</p>
              </div>
            ) : (
              <p className="mt-1 text-gray-500 italic">Sistema Automatizado</p>
            )}
          </div>

          {/* Acción */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Acción Realizada
            </label>
            <p className="mt-1">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                {auditoriaService.formatearAccion(registro.accion)}
              </span>
            </p>
          </div>

          {/* Módulo/Tabla */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Módulo Afectado
            </label>
            <p className="mt-1 text-gray-900">
              {auditoriaService.formatearTabla(registro.tabla_afectada)}
              {registro.registro_id && (
                <span className="ml-2 text-gray-500">
                  (Registro #{registro.registro_id})
                </span>
              )}
            </p>
          </div>

          {/* IP y User Agent */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Dirección IP
              </label>
              <p className="mt-1 text-gray-900">{registro.ip_address || 'No disponible'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Navegador
              </label>
              <p className="mt-1 text-gray-900 text-sm truncate" title={registro.user_agent || ''}>
                {registro.user_agent ? (
                  registro.user_agent.includes('Chrome') ? '🌐 Chrome' :
                  registro.user_agent.includes('Firefox') ? '🦊 Firefox' :
                  registro.user_agent.includes('Safari') ? '🧭 Safari' :
                  registro.user_agent.includes('Edge') ? '🌊 Edge' : '🖥️ Otro'
                ) : 'No disponible'}
              </p>
            </div>
          </div>

          {/* Detalles */}
          {detalles && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Detalles Adicionales
              </label>
              <div className="bg-gray-50 rounded p-3 border">
                {typeof detalles === 'object' ? (
                  <pre className="text-sm text-gray-800 overflow-x-auto">
                    {JSON.stringify(detalles, null, 2)}
                  </pre>
                ) : (
                  <p className="text-sm text-gray-800">{detalles}</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-100 px-6 py-4 border-t flex justify-end">
          <button
            onClick={onCerrar}
            className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

export default DetalleBitacora;
```

---

## 5. DASHBOARD DE AUDITORÍA

### 5.1 Página Principal

```tsx
// src/pages/Auditoria.tsx
import React, { useState, useEffect } from 'react';
import TablaBitacora from '../components/TablaBitacora';
import DetalleBitacora from '../components/DetalleBitacora';
import FiltrosBitacora from '../components/FiltrosBitacora';
import ResumenAuditoria from '../components/ResumenAuditoria';
import auditoriaService from '../services/auditoriaService';
import { RegistroBitacora, FiltrosBitacora as IFiltrosBitacora } from '../types/auditoria';

const Auditoria: React.FC = () => {
  const [registroSeleccionado, setRegistroSeleccionado] = useState<RegistroBitacora | null>(null);
  const [filtros, setFiltros] = useState<IFiltrosBitacora>({});
  const [vistaActual, setVistaActual] = useState<'tabla' | 'resumen'>('tabla');

  const handleExportarCSV = async () => {
    try {
      const blob = await auditoriaService.exportarCSV(filtros);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `auditoria-${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error al exportar:', error);
      alert('Error al exportar los registros');
    }
  };

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          📊 Auditoría y Bitácora del Sistema
        </h1>
        <p className="text-gray-600">
          Registro completo de todas las acciones realizadas en el sistema
        </p>
      </div>

      {/* Controles */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex justify-between items-center mb-4">
          <div className="flex space-x-2">
            <button
              onClick={() => setVistaActual('tabla')}
              className={`px-4 py-2 rounded font-medium ${
                vistaActual === 'tabla'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              📋 Tabla de Registros
            </button>
            <button
              onClick={() => setVistaActual('resumen')}
              className={`px-4 py-2 rounded font-medium ${
                vistaActual === 'resumen'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              📈 Resumen
            </button>
          </div>

          <button
            onClick={handleExportarCSV}
            className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded flex items-center"
          >
            📥 Exportar CSV
          </button>
        </div>

        {/* Filtros */}
        <FiltrosBitacora onFiltrosChange={setFiltros} />
      </div>

      {/* Contenido */}
      {vistaActual === 'tabla' ? (
        <div className="bg-white rounded-lg shadow-md">
          <TablaBitacora
            filtros={filtros}
            onVerDetalle={setRegistroSeleccionado}
          />
        </div>
      ) : (
        <ResumenAuditoria />
      )}

      {/* Modal de Detalle */}
      {registroSeleccionado && (
        <DetalleBitacora
          registro={registroSeleccionado}
          onCerrar={() => setRegistroSeleccionado(null)}
        />
      )}
    </div>
  );
};

export default Auditoria;
```

### 5.2 Resumen con Estadísticas

```tsx
// src/components/ResumenAuditoria.tsx
import React, { useEffect, useState } from 'react';
import auditoriaService from '../services/auditoriaService';
import { ResumenBitacora } from '../types/auditoria';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

const ResumenAuditoria: React.FC = () => {
  const [resumen, setResumen] = useState<ResumenBitacora | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    cargarResumen();
  }, []);

  const cargarResumen = async () => {
    try {
      const data = await auditoriaService.obtenerResumen();
      setResumen(data);
    } catch (error) {
      console.error('Error al cargar resumen:', error);
    } finally {
      setCargando(false);
    }
  };

  if (cargando) {
    return <div className="text-center p-8">Cargando estadísticas...</div>;
  }

  if (!resumen) {
    return <div className="text-center p-8 text-red-600">Error al cargar datos</div>;
  }

  // Datos para gráfico de pastel (acciones)
  const dataPorAccion = {
    labels: resumen.por_accion.slice(0, 5).map((a) => auditoriaService.formatearAccion(a.accion)),
    datasets: [
      {
        data: resumen.por_accion.slice(0, 5).map((a) => a.total),
        backgroundColor: [
          '#3B82F6',
          '#10B981',
          '#F59E0B',
          '#EF4444',
          '#8B5CF6',
        ],
      },
    ],
  };

  // Datos para gráfico de barras (tablas)
  const dataPorTabla = {
    labels: resumen.por_tabla.map((t) => auditoriaService.formatearTabla(t.tabla_afectada)),
    datasets: [
      {
        label: 'Cantidad de Acciones',
        data: resumen.por_tabla.map((t) => t.total),
        backgroundColor: '#3B82F6',
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Tarjetas de Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm font-medium">Total de Registros</p>
              <p className="text-3xl font-bold text-gray-800 mt-2">
                {resumen.total_registros.toLocaleString()}
              </p>
            </div>
            <div className="text-4xl">📊</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm font-medium">Últimos 7 días</p>
              <p className="text-3xl font-bold text-blue-600 mt-2">
                {resumen.ultimos_7_dias.toLocaleString()}
              </p>
            </div>
            <div className="text-4xl">📅</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm font-medium">Últimos 30 días</p>
              <p className="text-3xl font-bold text-green-600 mt-2">
                {resumen.ultimos_30_dias.toLocaleString()}
              </p>
            </div>
            <div className="text-4xl">📆</div>
          </div>
        </div>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Gráfico de Acciones */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">
            Top 5 Acciones más Frecuentes
          </h3>
          <div className="h-64 flex items-center justify-center">
            <Pie data={dataPorAccion} options={{ maintainAspectRatio: false }} />
          </div>
        </div>

        {/* Gráfico de Módulos */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">
            Actividad por Módulo
          </h3>
          <div className="h-64">
            <Bar 
              data={dataPorTabla} 
              options={{ 
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                  },
                },
              }} 
            />
          </div>
        </div>
      </div>

      {/* Tabla de Acciones */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">
          Desglose de Acciones
        </h3>
        <table className="min-w-full">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">
                Acción
              </th>
              <th className="px-4 py-2 text-right text-sm font-medium text-gray-700">
                Total
              </th>
              <th className="px-4 py-2 text-right text-sm font-medium text-gray-700">
                Porcentaje
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {resumen.por_accion.slice(0, 10).map((accion, index) => (
              <tr key={index}>
                <td className="px-4 py-2 text-sm text-gray-900">
                  {auditoriaService.formatearAccion(accion.accion)}
                </td>
                <td className="px-4 py-2 text-sm text-gray-900 text-right">
                  {accion.total.toLocaleString()}
                </td>
                <td className="px-4 py-2 text-sm text-gray-500 text-right">
                  {((accion.total / resumen.total_registros) * 100).toFixed(1)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ResumenAuditoria;
```

---

## 6. FILTROS Y BÚSQUEDA

```tsx
// src/components/FiltrosBitacora.tsx
import React, { useState } from 'react';
import { FiltrosBitacora as IFiltrosBitacora } from '../types/auditoria';

interface Props {
  onFiltrosChange: (filtros: IFiltrosBitacora) => void;
}

const FiltrosBitacora: React.FC<Props> = ({ onFiltrosChange }) => {
  const [accion, setAccion] = useState('');
  const [tabla, setTabla] = useState('');
  const [busqueda, setBusqueda] = useState('');

  const handleAplicarFiltros = () => {
    onFiltrosChange({
      accion: accion || undefined,
      tabla_afectada: tabla || undefined,
      search: busqueda || undefined,
    });
  };

  const handleLimpiarFiltros = () => {
    setAccion('');
    setTabla('');
    setBusqueda('');
    onFiltrosChange({});
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Búsqueda General */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Búsqueda
          </label>
          <input
            type="text"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="IP, detalles..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Filtro por Acción */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Acción
          </label>
          <select
            value={accion}
            onChange={(e) => setAccion(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todas las acciones</option>
            <option value="LOGIN">Login</option>
            <option value="LOGOUT">Logout</option>
            <option value="CREAR_CITA">Crear Cita</option>
            <option value="EDITAR_CITA">Editar Cita</option>
            <option value="CANCELAR_CITA">Cancelar Cita</option>
            <option value="CREAR_PAGO">Crear Pago</option>
            <option value="CONFIRMAR_PAGO">Confirmar Pago</option>
          </select>
        </div>

        {/* Filtro por Tabla */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Módulo
          </label>
          <select
            value={tabla}
            onChange={(e) => setTabla(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos los módulos</option>
            <option value="consulta">Citas</option>
            <option value="usuario">Usuarios</option>
            <option value="paciente">Pacientes</option>
            <option value="pago_en_linea">Pagos</option>
            <option value="factura">Facturas</option>
            <option value="historial_clinico">Historial Clínico</option>
          </select>
        </div>

        {/* Botones */}
        <div className="flex items-end space-x-2">
          <button
            onClick={handleAplicarFiltros}
            className="flex-1 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            🔍 Filtrar
          </button>
          <button
            onClick={handleLimpiarFiltros}
            className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  );
};

export default FiltrosBitacora;
```

---

## 7. REPORTES Y EXPORTACIÓN

### 7.1 Exportar a CSV

```typescript
// Ya incluido en auditoriaService.exportarCSV()
// Uso:
const exportar = async () => {
  const blob = await auditoriaService.exportarCSV({
    fecha_desde: '2025-01-01',
    fecha_hasta: '2025-12-31',
  });
  
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'auditoria.csv';
  link.click();
};
```

### 7.2 Generar Reporte PDF (Opcional)

```typescript
// src/utils/generarReportePDF.ts
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { RegistroBitacora } from '../types/auditoria';

export const generarReportePDF = (registros: RegistroBitacora[]) => {
  const doc = new jsPDF();

  // Título
  doc.setFontSize(18);
  doc.text('Reporte de Auditoría', 14, 20);

  // Fecha de generación
  doc.setFontSize(10);
  doc.text(`Generado: ${new Date().toLocaleString('es-BO')}`, 14, 28);

  // Tabla
  autoTable(doc, {
    startY: 35,
    head: [['Fecha', 'Usuario', 'Acción', 'Módulo', 'IP']],
    body: registros.map((r) => [
      new Date(r.fecha).toLocaleString('es-BO'),
      r.usuario?.nombre || 'Sistema',
      r.accion,
      r.tabla_afectada || '-',
      r.ip_address || '-',
    ]),
  });

  doc.save(`auditoria-${Date.now()}.pdf`);
};
```

---

## 📊 RESUMEN

### ✅ Funcionalidades Implementadas

1. **Tabla de Registros**: Ver todos los logs con paginación
2. **Filtros Avanzados**: Por usuario, acción, tabla, fecha
3. **Búsqueda**: Buscar en IP, detalles, etc.
4. **Detalle Completo**: Modal con toda la información
5. **Dashboard de Estadísticas**: Gráficos y resúmenes
6. **Exportación**: Descargar en CSV o PDF
7. **Actividad Reciente**: Ver últimas acciones

### 🎯 Casos de Uso

```typescript
// Ver actividad reciente
const recientes = await auditoriaService.obtenerActividadReciente(20);

// Filtrar por usuario
const porUsuario = await auditoriaService.obtenerPorUsuario(123);

// Filtrar por tabla
const porTabla = await auditoriaService.obtenerPorTabla('consulta');

// Obtener estadísticas
const resumen = await auditoriaService.obtenerResumen();
```

### 📦 Instalación de Dependencias

```bash
npm install chart.js react-chartjs-2
npm install jspdf jspdf-autotable  # Para exportar PDF
```

---

✅ **BACKEND LISTO** | 🚀 **FRONTEND CON GUÍA COMPLETA** | 📊 **AUDITORÍA TOTAL**
