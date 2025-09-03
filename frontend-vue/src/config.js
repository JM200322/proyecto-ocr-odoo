// frontend-vue/src/config.js

// Configuración automática del backend
export const BACKEND_URL = 
  process.env.NODE_ENV === 'production' 
    ? '' // En producción, usar URL relativa (mismo servidor)
    : 'http://localhost:5000'; // En desarrollo

console.log('🔧 Backend URL:', BACKEND_URL || 'Relative URL (same origin)');
console.log('🌍 Environment:', process.env.NODE_ENV);