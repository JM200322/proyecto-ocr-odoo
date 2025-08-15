// Configuración del Backend
// Para DESARROLLO LOCAL (localhost)
export const BACKEND_URL = 'http://127.0.0.1:5000';

// Para PRODUCCIÓN (Render)
// export const BACKEND_URL = 'https://proyecto-ocr-odoo-1.onrender.com';

// Para DESARROLLO LOCAL con IP específica (si localhost no funciona)
// export const BACKEND_URL = 'http://127.0.0.1:5000';

console.log('🔧 Configuración del Backend:');
console.log('📍 URL configurada:', BACKEND_URL);
console.log('🌐 Entorno:', BACKEND_URL.includes('localhost') || BACKEND_URL.includes('127.0.0.1') ? 'DESARROLLO LOCAL' : 'PRODUCCIÓN');