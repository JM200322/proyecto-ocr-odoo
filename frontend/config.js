// Configuración del Backend
// Cambia esta variable según tu entorno

// Para DESARROLLO LOCAL (localhost)
// const BACKEND_URL = 'http://localhost:5000';

// Para PRODUCCIÓN (Render) - Descomenta la línea de abajo y comenta la de arriba
const BACKEND_URL = 'https://proyecto-ocr-odoo-1.onrender.com';

// Para DESARROLLO LOCAL con IP específica (si localhost no funciona)
// const BACKEND_URL = 'http://127.0.0.1:5000';

console.log('🔧 Configuración del Backend:');
console.log('📍 URL configurada:', BACKEND_URL);
console.log('🌐 Entorno:', BACKEND_URL.includes('localhost') || BACKEND_URL.includes('127.0.0.1') ? 'DESARROLLO LOCAL' : 'PRODUCCIÓN');

// Exportar para uso en otros archivos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BACKEND_URL };
} 