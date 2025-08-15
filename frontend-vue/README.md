# OCR Odoo Integration Tool - Vue.js Frontend v3.0

Frontend moderno construido con Vue.js para el sistema de OCR con integración Odoo.

## Características

- **Vue.js 3** con Composition API
- **Vite** como herramienta de desarrollo
- **Componentes modulares** y reutilizables
- **Procesamiento OCR avanzado** con OCR.Space API
- **Interfaz responsive** y moderna
- **Debug integrado** y métricas en tiempo real

## Estructura del proyecto

```
frontend-vue/
├── src/
│   ├── components/          # Componentes Vue
│   │   ├── AppHeader.vue
│   │   ├── CameraComponent.vue
│   │   ├── OCRResults.vue
│   │   ├── StatisticsDisplay.vue
│   │   └── ...
│   ├── assets/             # Estilos CSS
│   ├── config.js           # Configuración del backend
│   ├── App.vue             # Componente principal
│   └── main.js             # Punto de entrada
├── public/                 # Archivos estáticos
├── package.json            # Dependencias
└── vite.config.js          # Configuración Vite
```

## Scripts disponibles

```bash
# Desarrollo (servidor en puerto 3000)
npm run dev

# Construcción para producción
npm run build

# Vista previa del build
npm run preview
```

## Configuración

Edita `src/config.js` para cambiar la URL del backend:

```javascript
// Para desarrollo local
export const BACKEND_URL = 'http://localhost:5000';

// Para producción
export const BACKEND_URL = 'https://proyecto-ocr-odoo-1.onrender.com';
```

## Componentes principales

- **CameraComponent**: Manejo de cámara, captura y marco de enfoque
- **OCRResults**: Visualización y edición de resultados OCR
- **StatisticsDisplay**: Métricas y estadísticas en tiempo real
- **DebugPanel**: Panel de depuración avanzado

## Características avanzadas

- Captura inteligente con marco de enfoque ajustable
- Procesamiento OCR con múltiples engines
- Sistema de caché integrado
- Atajos de teclado (Espacio, Escape, Ctrl+D)
- Efectos visuales y UX optimizada