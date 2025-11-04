// ============================================
// utils/tenant.js
// Detección dinámica de tenant por subdominio
// ============================================

/**
 * Detecta el subdominio actual y retorna información del tenant
 */
export const getTenantInfo = () => {
  const hostname = window.location.hostname;
  const parts = hostname.split('.');
  
  const isDevelopment = import.meta.env.DEV;
  const baseDomain = import.meta.env.VITE_DOMAIN_BASE || 'psicoadmin.xyz';
  
  let subdomain = null;
  let isPublic = false;
  
  // DESARROLLO LOCAL (*.localhost:5173)
  if (isDevelopment || hostname.includes('localhost')) {
    if (parts.length > 1 && parts[0] !== 'localhost') {
      subdomain = parts[0]; // clinica1.localhost -> 'clinica1'
    } else {
      isPublic = true; // localhost -> público
    }
  }
  // PRODUCCIÓN (*.psicoadmin.xyz)
  else {
    if (parts.length > 2) {
      subdomain = parts[0]; // clinica1.psicoadmin.xyz -> 'clinica1'
    } else if (hostname === baseDomain || hostname === `www.${baseDomain}`) {
      isPublic = true; // psicoadmin.xyz -> público
    }
  }
  
  return {
    subdomain,
    isPublic,
    hostname,
    tenantId: subdomain || 'public',
    displayName: subdomain 
      ? `Clínica ${subdomain.charAt(0).toUpperCase() + subdomain.slice(1)}` 
      : 'Sistema Central',
    fullUrl: window.location.href
  };
};

/**
 * Obtiene la URL base del API según el tenant
 */
export const getApiBaseUrl = () => {
  const isDevelopment = import.meta.env.DEV;
  
  if (isDevelopment) {
    return 'http://localhost:8000/api';
  }
  
  // Producción: usar dominio del backend en Render
  return 'https://clinicadental-backend.onrender.com/api';
};

/**
 * Header personalizado con subdominio para el backend
 */
export const getTenantHeader = () => {
  const { subdomain } = getTenantInfo();
  // Django-tenants usa el hostname, pero podemos enviar un header adicional
  return subdomain ? { 'X-Tenant-Subdomain': subdomain } : {};
};

/**
 * Valida acceso al tenant
 */
export const validateTenantAccess = (userTenant, currentTenant) => {
  if (userTenant === 'public' || userTenant === 'admin') {
    return true;
  }
  return userTenant === currentTenant;
};

/**
 * Redirige al tenant correcto
 */
export const redirectToTenant = (tenantId) => {
  const isDevelopment = import.meta.env.DEV;
  const currentTenant = getTenantInfo().tenantId;
  
  if (currentTenant === tenantId) return;
  
  let targetUrl;
  if (isDevelopment) {
    targetUrl = tenantId === 'public' 
      ? 'http://localhost:5173'
      : `http://${tenantId}.localhost:5173`;
  } else {
    targetUrl = tenantId === 'public'
      ? 'https://psicoadmin.xyz'
      : `https://${tenantId}.psicoadmin.xyz`;
  }
  
  window.location.href = targetUrl;
};

// ============================================
// Exports
// ============================================
export default {
  getTenantInfo,
  getApiBaseUrl,
  getTenantHeader,
  validateTenantAccess,
  redirectToTenant
};
