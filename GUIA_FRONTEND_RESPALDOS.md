# 📦 Guía Frontend - Sistema de Respaldos Automáticos

## 🎯 Objetivo

Implementar la interfaz de usuario para gestionar respaldos automáticos en la nube, permitiendo a los administradores de cada clínica:
- Ver listado de respaldos
- Crear respaldos manuales
- Descargar respaldos
- Ver estadísticas y detalles
- Eliminar respaldos antiguos

---

## 📋 Tabla de Contenidos

1. [Servicio API (respaldoService.ts)](#1-servicio-api)
2. [Tipos TypeScript (types.ts)](#2-tipos-typescript)
3. [Lista de Respaldos (RespaldosList.tsx)](#3-lista-de-respaldos)
4. [Crear Respaldo Manual (CrearRespaldo.tsx)](#4-crear-respaldo-manual)
5. [Detalles del Respaldo (RespaldoDetail.tsx)](#5-detalles-del-respaldo)
6. [Estadísticas (EstadisticasRespaldos.tsx)](#6-estadísticas)
7. [Routing y Navegación](#7-routing-y-navegación)
8. [Integración Completa](#8-integración-completa)

---

## 1. Servicio API

### 📁 `src/services/respaldoService.ts`

```typescript
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Interfaces
export interface Respaldo {
  id: number;
  clinica_id: number;
  fecha_respaldo: string;
  tamaño_bytes: number;
  tamaño_mb: number;
  numero_registros: number;
  estado: 'pendiente' | 'procesando' | 'completado' | 'fallido' | 'cancelado';
  estado_display: string;
  tipo_respaldo: 'manual' | 'automatico' | 'por_demanda';
  tipo_respaldo_display: string;
  descripcion: string;
  usuario: number | null;
  fecha_creacion: string;
  puede_restaurar: boolean;
}

export interface RespaldoDetail extends Respaldo {
  archivo_s3: string;
  hash_md5: string;
  tiempo_ejecucion: string;
  tiempo_ejecucion_segundos: number;
  metadata: {
    modelos_respaldados: string[];
    detalles_registros: Record<string, number>;
    tamaño_original_mb: number;
    tamaño_comprimido_mb: number;
    compresion_porcentaje: number;
  };
  usuario_nombre: string | null;
  fecha_actualizacion: string;
}

export interface Estadisticas {
  total_respaldos: number;
  completados: number;
  fallidos: number;
  tamaño_total_mb: number;
  ultimo_respaldo: {
    id: number;
    fecha: string;
    tamaño_mb: number;
  } | null;
}

export interface CrearRespaldoRequest {
  descripcion?: string;
}

export interface DescargarRespaldoResponse {
  url: string;
  expira_en_segundos: number;
  archivo: string;
  tamaño_mb: number;
}

// Obtener token del localStorage
const getToken = () => {
  return localStorage.getItem('token') || '';
};

// Headers con autenticación
const getHeaders = () => ({
  'Authorization': `Token ${getToken()}`,
  'Content-Type': 'application/json',
});

// Servicio de Respaldos
const respaldoService = {
  /**
   * Listar todos los respaldos de la clínica del usuario autenticado
   */
  async listarRespaldos(): Promise<Respaldo[]> {
    try {
      const response = await axios.get(`${API_URL}/api/v1/respaldos/`, {
        headers: getHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error al listar respaldos:', error);
      throw error;
    }
  },

  /**
   * Obtener detalles de un respaldo específico
   */
  async obtenerRespaldo(id: number): Promise<RespaldoDetail> {
    try {
      const response = await axios.get(`${API_URL}/api/v1/respaldos/${id}/`, {
        headers: getHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error(`Error al obtener respaldo ${id}:`, error);
      throw error;
    }
  },

  /**
   * Crear respaldo manual/por demanda
   */
  async crearRespaldoManual(data: CrearRespaldoRequest): Promise<{
    mensaje: string;
    respaldo: RespaldoDetail;
  }> {
    try {
      const response = await axios.post(
        `${API_URL}/api/v1/respaldos/crear_respaldo_manual/`,
        data,
        { headers: getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error al crear respaldo manual:', error);
      throw error;
    }
  },

  /**
   * Obtener URL de descarga temporal (válida por 1 hora)
   */
  async obtenerUrlDescarga(id: number): Promise<DescargarRespaldoResponse> {
    try {
      const response = await axios.get(
        `${API_URL}/api/v1/respaldos/${id}/descargar/`,
        { headers: getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error(`Error al obtener URL de descarga para respaldo ${id}:`, error);
      throw error;
    }
  },

  /**
   * Eliminar respaldo (soft delete)
   */
  async eliminarRespaldo(id: number): Promise<void> {
    try {
      await axios.delete(`${API_URL}/api/v1/respaldos/${id}/`, {
        headers: getHeaders(),
      });
    } catch (error) {
      console.error(`Error al eliminar respaldo ${id}:`, error);
      throw error;
    }
  },

  /**
   * Obtener estadísticas de respaldos
   */
  async obtenerEstadisticas(): Promise<Estadisticas> {
    try {
      const response = await axios.get(
        `${API_URL}/api/v1/respaldos/estadisticas/`,
        { headers: getHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Error al obtener estadísticas:', error);
      throw error;
    }
  },

  /**
   * Descargar archivo de respaldo
   */
  async descargarArchivo(id: number): Promise<void> {
    try {
      // Primero obtener la URL prefirmada
      const { url, archivo } = await this.obtenerUrlDescarga(id);
      
      // Crear link temporal y hacer clic programáticamente
      const link = document.createElement('a');
      link.href = url;
      link.download = archivo.split('/').pop() || `respaldo_${id}.json.gz`;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error(`Error al descargar respaldo ${id}:`, error);
      throw error;
    }
  },
};

export default respaldoService;
```

---

## 2. Tipos TypeScript

### 📁 `src/types/respaldo.types.ts`

```typescript
export type EstadoRespaldo = 'pendiente' | 'procesando' | 'completado' | 'fallido' | 'cancelado';
export type TipoRespaldo = 'manual' | 'automatico' | 'por_demanda';

export interface Respaldo {
  id: number;
  clinica_id: number;
  fecha_respaldo: string;
  tamaño_bytes: number;
  tamaño_mb: number;
  numero_registros: number;
  estado: EstadoRespaldo;
  estado_display: string;
  tipo_respaldo: TipoRespaldo;
  tipo_respaldo_display: string;
  descripcion: string;
  usuario: number | null;
  fecha_creacion: string;
  puede_restaurar: boolean;
}

export interface RespaldoDetail extends Respaldo {
  archivo_s3: string;
  hash_md5: string;
  tiempo_ejecucion: string;
  tiempo_ejecucion_segundos: number;
  metadata: {
    modelos_respaldados: string[];
    detalles_registros: Record<string, number>;
    tamaño_original_mb: number;
    tamaño_comprimido_mb: number;
    compresion_porcentaje: number;
  };
  usuario_nombre: string | null;
  fecha_actualizacion: string;
}
```

---

## 3. Lista de Respaldos

### 📁 `src/components/Respaldos/RespaldosList.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Info as InfoIcon,
  CloudDownload as CloudDownloadIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import respaldoService, { Respaldo } from '../../services/respaldoService';
import CrearRespaldo from './CrearRespaldo';
import RespaldoDetail from './RespaldoDetail';

const RespaldosList: React.FC = () => {
  const [respaldos, setRespaldos] = useState<Respaldo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openCrear, setOpenCrear] = useState(false);
  const [selectedRespaldo, setSelectedRespaldo] = useState<number | null>(null);
  const [descargando, setDescargando] = useState<number | null>(null);

  // Cargar respaldos
  const cargarRespaldos = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await respaldoService.listarRespaldos();
      setRespaldos(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar respaldos');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarRespaldos();
  }, []);

  // Descargar respaldo
  const handleDescargar = async (id: number) => {
    try {
      setDescargando(id);
      await respaldoService.descargarArchivo(id);
    } catch (err: any) {
      alert(err.response?.data?.error || 'Error al descargar respaldo');
    } finally {
      setDescargando(null);
    }
  };

  // Eliminar respaldo
  const handleEliminar = async (id: number) => {
    if (!window.confirm('¿Estás seguro de eliminar este respaldo?')) return;

    try {
      await respaldoService.eliminarRespaldo(id);
      cargarRespaldos();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Error al eliminar respaldo');
    }
  };

  // Obtener color según estado
  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case 'completado':
        return 'success';
      case 'procesando':
        return 'info';
      case 'fallido':
        return 'error';
      case 'pendiente':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Obtener icono según tipo
  const getTipoIcon = (tipo: string) => {
    switch (tipo) {
      case 'automatico':
        return '🤖';
      case 'manual':
        return '👤';
      case 'por_demanda':
        return '⚡';
      default:
        return '📦';
    }
  };

  // Formatear fecha
  const formatFecha = (fecha: string) => {
    return format(new Date(fecha), "d 'de' MMMM yyyy, HH:mm", { locale: es });
  };

  // Formatear tamaño
  const formatTamaño = (mb: number) => {
    if (mb < 1) return `${(mb * 1024).toFixed(2)} KB`;
    if (mb < 1024) return `${mb.toFixed(2)} MB`;
    return `${(mb / 1024).toFixed(2)} GB`;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          <CloudDownloadIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Respaldos en la Nube
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={cargarRespaldos}
            sx={{ mr: 1 }}
          >
            Actualizar
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenCrear(true)}
          >
            Crear Respaldo
          </Button>
        </Box>
      </Box>

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Tabla de Respaldos */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Tipo</TableCell>
              <TableCell>Fecha</TableCell>
              <TableCell>Tamaño</TableCell>
              <TableCell>Registros</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell>Descripción</TableCell>
              <TableCell align="center">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {respaldos.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography variant="body2" color="text.secondary" py={3}>
                    No hay respaldos disponibles. Crea tu primer respaldo.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              respaldos.map((respaldo) => (
                <TableRow key={respaldo.id} hover>
                  <TableCell>#{respaldo.id}</TableCell>
                  <TableCell>
                    <Tooltip title={respaldo.tipo_respaldo_display}>
                      <span style={{ fontSize: '1.2em' }}>
                        {getTipoIcon(respaldo.tipo_respaldo)}
                      </span>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatFecha(respaldo.fecha_respaldo)}
                    </Typography>
                  </TableCell>
                  <TableCell>{formatTamaño(respaldo.tamaño_mb)}</TableCell>
                  <TableCell>
                    {respaldo.numero_registros.toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={respaldo.estado_display}
                      color={getEstadoColor(respaldo.estado) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap maxWidth={200}>
                      {respaldo.descripcion || '—'}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title="Ver detalles">
                      <IconButton
                        size="small"
                        onClick={() => setSelectedRespaldo(respaldo.id)}
                      >
                        <InfoIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Descargar">
                      <span>
                        <IconButton
                          size="small"
                          onClick={() => handleDescargar(respaldo.id)}
                          disabled={
                            respaldo.estado !== 'completado' ||
                            descargando === respaldo.id
                          }
                        >
                          {descargando === respaldo.id ? (
                            <CircularProgress size={20} />
                          ) : (
                            <DownloadIcon />
                          )}
                        </IconButton>
                      </span>
                    </Tooltip>
                    <Tooltip title="Eliminar">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleEliminar(respaldo.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Modales */}
      <CrearRespaldo
        open={openCrear}
        onClose={() => setOpenCrear(false)}
        onCreated={cargarRespaldos}
      />

      {selectedRespaldo && (
        <RespaldoDetail
          respaldoId={selectedRespaldo}
          open={!!selectedRespaldo}
          onClose={() => setSelectedRespaldo(null)}
        />
      )}
    </Box>
  );
};

export default RespaldosList;
```

---

## 4. Crear Respaldo Manual

### 📁 `src/components/Respaldos/CrearRespaldo.tsx`

```typescript
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  CircularProgress,
  Alert,
  Box,
  Typography,
} from '@mui/material';
import { BackupOutlined as BackupIcon } from '@mui/icons-material';
import respaldoService from '../../services/respaldoService';

interface CrearRespaldoProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

const CrearRespaldo: React.FC<CrearRespaldoProps> = ({ open, onClose, onCreated }) => {
  const [descripcion, setDescripcion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(false);

      const response = await respaldoService.crearRespaldoManual({
        descripcion: descripcion.trim() || undefined,
      });

      setSuccess(true);
      setTimeout(() => {
        onCreated();
        handleClose();
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al crear respaldo');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setDescripcion('');
      setError(null);
      setSuccess(false);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center">
          <BackupIcon sx={{ mr: 1 }} />
          Crear Respaldo Manual
        </Box>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ pt: 1 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              ✅ Respaldo creado exitosamente. Se está procesando en segundo plano.
            </Alert>
          )}

          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Se creará un respaldo completo de todos los datos de tu clínica.
            Este proceso puede tardar varios segundos dependiendo de la cantidad de información.
          </Typography>

          <TextField
            label="Descripción (opcional)"
            placeholder="Ej: Respaldo antes de actualización importante"
            fullWidth
            multiline
            rows={3}
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            disabled={loading || success}
            helperText="Agrega una nota para identificar este respaldo"
          />
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancelar
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading || success}
          startIcon={loading ? <CircularProgress size={20} /> : <BackupIcon />}
        >
          {loading ? 'Creando...' : 'Crear Respaldo'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CrearRespaldo;
```

---

## 5. Detalles del Respaldo

### 📁 `src/components/Respaldos/RespaldoDetail.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  CircularProgress,
  Alert,
  Box,
  Typography,
  Grid,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  Paper,
} from '@mui/material';
import {
  Info as InfoIcon,
  Download as DownloadIcon,
  Storage as StorageIcon,
  Timer as TimerIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import respaldoService, { RespaldoDetail as RespaldoDetailType } from '../../services/respaldoService';

interface RespaldoDetailProps {
  respaldoId: number;
  open: boolean;
  onClose: () => void;
}

const RespaldoDetail: React.FC<RespaldoDetailProps> = ({ respaldoId, open, onClose }) => {
  const [respaldo, setRespaldo] = useState<RespaldoDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [descargando, setDescargando] = useState(false);

  useEffect(() => {
    if (open && respaldoId) {
      cargarRespaldo();
    }
  }, [respaldoId, open]);

  const cargarRespaldo = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await respaldoService.obtenerRespaldo(respaldoId);
      setRespaldo(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar detalles');
    } finally {
      setLoading(false);
    }
  };

  const handleDescargar = async () => {
    try {
      setDescargando(true);
      await respaldoService.descargarArchivo(respaldoId);
    } catch (err: any) {
      alert(err.response?.data?.error || 'Error al descargar respaldo');
    } finally {
      setDescargando(false);
    }
  };

  const formatFecha = (fecha: string) => {
    return format(new Date(fecha), "d 'de' MMMM yyyy, HH:mm:ss", { locale: es });
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center">
          <InfoIcon sx={{ mr: 1 }} />
          Detalles del Respaldo #{respaldoId}
        </Box>
      </DialogTitle>

      <DialogContent>
        {loading ? (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : respaldo ? (
          <Box>
            {/* Información General */}
            <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default', mb: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="caption" color="text.secondary">
                    Fecha de Creación
                  </Typography>
                  <Typography variant="body1">
                    {formatFecha(respaldo.fecha_respaldo)}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="caption" color="text.secondary">
                    Estado
                  </Typography>
                  <Box>
                    <Chip
                      label={respaldo.estado_display}
                      color={respaldo.estado === 'completado' ? 'success' : 'default'}
                      size="small"
                      icon={respaldo.estado === 'completado' ? <CheckCircleIcon /> : undefined}
                    />
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="caption" color="text.secondary">
                    Tipo
                  </Typography>
                  <Typography variant="body1">
                    {respaldo.tipo_respaldo_display}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="caption" color="text.secondary">
                    Creado por
                  </Typography>
                  <Typography variant="body1">
                    {respaldo.usuario_nombre || 'Sistema'}
                  </Typography>
                </Grid>
              </Grid>
            </Paper>

            {/* Estadísticas */}
            <Typography variant="h6" gutterBottom>
              <StorageIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Estadísticas
            </Typography>
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={6} md={3}>
                <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {respaldo.numero_registros.toLocaleString()}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Registros
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6} md={3}>
                <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {respaldo.tamaño_mb.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    MB Comprimido
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6} md={3}>
                <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {respaldo.metadata?.compresion_porcentaje?.toFixed(1) || 0}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Compresión
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={6} md={3}>
                <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {respaldo.tiempo_ejecucion_segundos.toFixed(1)}s
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Tiempo
                  </Typography>
                </Paper>
              </Grid>
            </Grid>

            {/* Detalles de Modelos */}
            {respaldo.metadata?.detalles_registros && (
              <>
                <Typography variant="h6" gutterBottom>
                  Modelos Respaldados
                </Typography>
                <List dense>
                  {Object.entries(respaldo.metadata.detalles_registros).map(([modelo, count]) => (
                    <ListItem key={modelo}>
                      <ListItemText
                        primary={modelo}
                        secondary={`${count} registro${count !== 1 ? 's' : ''}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </>
            )}

            <Divider sx={{ my: 2 }} />

            {/* Información Técnica */}
            <Typography variant="caption" color="text.secondary" display="block">
              Archivo S3: {respaldo.archivo_s3}
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              Hash MD5: {respaldo.hash_md5}
            </Typography>

            {respaldo.descripcion && (
              <>
                <Divider sx={{ my: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  <strong>Descripción:</strong> {respaldo.descripcion}
                </Typography>
              </>
            )}
          </Box>
        ) : null}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cerrar</Button>
        {respaldo?.estado === 'completado' && (
          <Button
            variant="contained"
            startIcon={descargando ? <CircularProgress size={20} /> : <DownloadIcon />}
            onClick={handleDescargar}
            disabled={descargando}
          >
            {descargando ? 'Descargando...' : 'Descargar'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default RespaldoDetail;
```

---

## 6. Estadísticas

### 📁 `src/components/Respaldos/EstadisticasRespaldos.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  Paper,
} from '@mui/material';
import {
  CloudDone as CloudDoneIcon,
  Error as ErrorIcon,
  Storage as StorageIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import respaldoService, { Estadisticas } from '../../services/respaldoService';

const EstadisticasRespaldos: React.FC = () => {
  const [stats, setStats] = useState<Estadisticas | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    cargarEstadisticas();
  }, []);

  const cargarEstadisticas = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await respaldoService.obtenerEstadisticas();
      setStats(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar estadísticas');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" py={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!stats) return null;

  const tasaExito = stats.total_respaldos > 0
    ? ((stats.completados / stats.total_respaldos) * 100).toFixed(1)
    : 0;

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" gutterBottom>
        Estadísticas de Respaldos
      </Typography>

      <Grid container spacing={3}>
        {/* Total Respaldos */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper elevation={2} sx={{ p: 3, textAlign: 'center' }}>
            <StorageIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
            <Typography variant="h3" color="primary">
              {stats.total_respaldos}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Respaldos
            </Typography>
          </Paper>
        </Grid>

        {/* Completados */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper elevation={2} sx={{ p: 3, textAlign: 'center' }}>
            <CloudDoneIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
            <Typography variant="h3" color="success.main">
              {stats.completados}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Completados ({tasaExito}%)
            </Typography>
          </Paper>
        </Grid>

        {/* Fallidos */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper elevation={2} sx={{ p: 3, textAlign: 'center' }}>
            <ErrorIcon sx={{ fontSize: 40, color: 'error.main', mb: 1 }} />
            <Typography variant="h3" color="error.main">
              {stats.fallidos}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Fallidos
            </Typography>
          </Paper>
        </Grid>

        {/* Tamaño Total */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper elevation={2} sx={{ p: 3, textAlign: 'center' }}>
            <StorageIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
            <Typography variant="h3" color="info.main">
              {stats.tamaño_total_mb.toFixed(1)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              MB Almacenados
            </Typography>
          </Paper>
        </Grid>

        {/* Último Respaldo */}
        {stats.ultimo_respaldo && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <ScheduleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Último Respaldo
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={4}>
                    <Typography variant="caption" color="text.secondary">
                      Fecha
                    </Typography>
                    <Typography variant="body1">
                      {format(new Date(stats.ultimo_respaldo.fecha), "d 'de' MMMM yyyy, HH:mm", {
                        locale: es,
                      })}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <Typography variant="caption" color="text.secondary">
                      ID
                    </Typography>
                    <Typography variant="body1">
                      #{stats.ultimo_respaldo.id}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <Typography variant="caption" color="text.secondary">
                      Tamaño
                    </Typography>
                    <Typography variant="body1">
                      {stats.ultimo_respaldo.tamaño_mb.toFixed(2)} MB
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default EstadisticasRespaldos;
```

---

## 7. Routing y Navegación

### 📁 Agregar a `src/App.tsx` o tu archivo de rutas

```typescript
import { Route, Routes } from 'react-router-dom';
import RespaldosList from './components/Respaldos/RespaldosList';
import EstadisticasRespaldos from './components/Respaldos/EstadisticasRespaldos';

// Dentro de tus rutas protegidas de admin
<Route path="/admin/respaldos" element={
  <Box>
    <EstadisticasRespaldos />
    <RespaldosList />
  </Box>
} />
```

### 📁 Agregar al menú de navegación

```typescript
// En tu componente de Sidebar/Menu
{
  title: 'Respaldos',
  path: '/admin/respaldos',
  icon: <CloudDownloadIcon />,
  roles: ['admin'], // Solo para administradores
}
```

---

## 8. Integración Completa

### Estructura de Carpetas Sugerida

```
src/
├── components/
│   └── Respaldos/
│       ├── RespaldosList.tsx
│       ├── CrearRespaldo.tsx
│       ├── RespaldoDetail.tsx
│       └── EstadisticasRespaldos.tsx
├── services/
│   └── respaldoService.ts
├── types/
│   └── respaldo.types.ts
└── App.tsx
```

### Variables de Entorno

Asegúrate de tener en `.env`:

```bash
VITE_API_URL=http://localhost:8000
```

---

## 🎨 Personalización

### Colores y Estilos

Puedes personalizar los colores en el tema de Material-UI:

```typescript
// theme.ts
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    success: {
      main: '#4caf50',
    },
    error: {
      main: '#f44336',
    },
  },
});
```

### Traducciones

Para traducir las fechas a español, asegúrate de tener instalado:

```bash
npm install date-fns
```

---

## 🧪 Testing

### Probar la Integración

1. **Iniciar backend**:
```bash
cd ClinicaDental-backend
python manage.py runserver
```

2. **Iniciar frontend**:
```bash
cd frontend
npm run dev
```

3. **Navegar a**: `http://localhost:5173/admin/respaldos`

4. **Crear primer respaldo** haciendo clic en "Crear Respaldo"

5. **Verificar** que aparece en la lista

6. **Descargar** el respaldo haciendo clic en el icono de descarga

---

## 📝 Checklist de Implementación

- [ ] Crear `respaldoService.ts`
- [ ] Crear `respaldo.types.ts`
- [ ] Crear componente `RespaldosList.tsx`
- [ ] Crear componente `CrearRespaldo.tsx`
- [ ] Crear componente `RespaldoDetail.tsx`
- [ ] Crear componente `EstadisticasRespaldos.tsx`
- [ ] Agregar rutas en `App.tsx`
- [ ] Agregar enlace en menú de navegación
- [ ] Configurar variable de entorno `VITE_API_URL`
- [ ] Probar crear respaldo
- [ ] Probar descargar respaldo
- [ ] Probar eliminar respaldo
- [ ] Verificar estadísticas

---

## 🚀 Funcionalidades Extras (Opcional)

### 1. Notificaciones en Tiempo Real

```typescript
// Usar WebSockets o polling para actualizar automáticamente
useEffect(() => {
  const interval = setInterval(() => {
    cargarRespaldos();
  }, 30000); // Cada 30 segundos

  return () => clearInterval(interval);
}, []);
```

### 2. Filtros y Búsqueda

```typescript
const [filtro, setFiltro] = useState('todos');
const respaldosFiltrados = respaldos.filter(r => 
  filtro === 'todos' || r.estado === filtro
);
```

### 3. Paginación

```typescript
import { Pagination } from '@mui/material';

const [page, setPage] = useState(1);
const itemsPerPage = 10;
const paginados = respaldos.slice(
  (page - 1) * itemsPerPage,
  page * itemsPerPage
);
```

---

## ✅ Resumen

Has implementado una interfaz completa de gestión de respaldos con:

✅ **Listar respaldos** con tabla interactiva
✅ **Crear respaldos manuales** con formulario modal
✅ **Ver detalles** con información completa
✅ **Descargar respaldos** con un clic
✅ **Eliminar respaldos** con confirmación
✅ **Estadísticas visuales** con tarjetas y gráficos

El sistema está **100% integrado** con el backend de Django y listo para usar.

---

## 📚 Recursos Adicionales

- [Material-UI Documentation](https://mui.com/)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [Axios Documentation](https://axios-http.com/)
- [date-fns Documentation](https://date-fns.org/)

---

¡Tu sistema de respaldos está completo! 🎉
