// ============================================
// services/api.js
// Cliente Axios configurado para multi-tenancy
// ============================================

import axios from 'axios';
import { getApiBaseUrl, getTenantHeader, getTenantInfo } from '../utils/tenant';

// Crear instancia de Axios
const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    ...getTenantHeader()
  }
});

// ============================================
// REQUEST INTERCEPTOR
// ============================================
api.interceptors.request.use(
  (config) => {
    // 1. Agregar token de autenticación
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    
    // 2. Re-agregar header de tenant (por si cambió)
    const tenantHeaders = getTenantHeader();
    config.headers = { ...config.headers, ...tenantHeaders };
    
    // 3. Log para debugging (remover en producción)
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, {
        tenant: getTenantInfo().tenantId,
        baseURL: config.baseURL
      });
    }
    
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// ============================================
// RESPONSE INTERCEPTOR
// ============================================
api.interceptors.response.use(
  (response) => {
    // Log exitoso (solo desarrollo)
    if (import.meta.env.DEV) {
      console.log(`[API] ✅ ${response.config.method?.toUpperCase()} ${response.config.url}`, response.status);
    }
    return response;
  },
  (error) => {
    // Obtener información del error
    const status = error.response?.status;
    const data = error.response?.data;
    const config = error.config;
    
    console.error(`[API] ❌ ${config?.method?.toUpperCase()} ${config?.url}`, {
      status,
      error: data
    });
    
    // CASO 1: Error 404 - Tenant no encontrado
    if (status === 404 && data?.error?.toLowerCase().includes('tenant')) {
      console.error('🏥 Tenant no encontrado:', getTenantInfo().tenantId);
      
      // Mostrar mensaje al usuario
      alert(`La clínica "${getTenantInfo().displayName}" no existe o no está activa.`);
      
      // Redirigir al sistema público
      const publicUrl = import.meta.env.DEV 
        ? 'http://localhost:5173'
        : 'https://psicoadmin.xyz';
      
      setTimeout(() => {
        window.location.href = publicUrl;
      }, 2000);
    }
    
    // CASO 2: Error 401 - No autenticado / Token expirado
    if (status === 401) {
      console.error('🔒 No autenticado o token expirado');
      
      // Limpiar autenticación
      localStorage.removeItem('authToken');
      localStorage.removeItem('userData');
      
      // Redirigir al login (mantener tenant actual)
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    
    // CASO 3: Error 403 - Sin permisos
    if (status === 403) {
      console.error('⛔ Acceso denegado');
      alert('No tienes permisos para realizar esta acción.');
    }
    
    // CASO 4: Error 500 - Error del servidor
    if (status === 500) {
      console.error('🔥 Error interno del servidor');
      alert('Ocurrió un error en el servidor. Por favor, inténtalo más tarde.');
    }
    
    return Promise.reject(error);
  }
);

// ============================================
// MÉTODOS AUXILIARES
// ============================================

/**
 * Manejo genérico de errores
 */
export const handleApiError = (error, customMessage = '') => {
  const message = error.response?.data?.error 
    || error.response?.data?.message 
    || error.message 
    || customMessage
    || 'Ocurrió un error inesperado';
  
  return {
    message,
    status: error.response?.status,
    data: error.response?.data
  };
};

/**
 * Verificar conexión con el backend
 */
export const checkConnection = async () => {
  try {
    const response = await api.get('/');
    return {
      connected: true,
      tenant: response.data.tenant,
      version: response.data.version
    };
  } catch (error) {
    return {
      connected: false,
      error: handleApiError(error)
    };
  }
};

// ============================================
// EXPORTS
// ============================================
export default api;
export { handleApiError, checkConnection };
