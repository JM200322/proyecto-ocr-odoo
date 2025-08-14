# 🔧 Configuración de Entornos - OCR.Space

## 📁 Archivo de Configuración

El archivo `frontend/config.js` controla la URL del backend según el entorno.

## 🏠 **DESARROLLO LOCAL (localhost)**

```javascript
// Para DESARROLLO LOCAL (localhost)
const BACKEND_URL = 'http://localhost:5000';

// Para PRODUCCIÓN (Render) - Comentada
// const BACKEND_URL = 'https://proyecto-ocr-odoo-1.onrender.com';
```

**Cuándo usar:** Cuando desarrollas localmente en tu computadora.

## 🌐 **PRODUCCIÓN (Render)**

```javascript
// Para DESARROLLO LOCAL (localhost) - Comentada
// const BACKEND_URL = 'http://localhost:5000';

// Para PRODUCCIÓN (Render)
const BACKEND_URL = 'https://proyecto-ocr-odoo-1.onrender.com';
```

**Cuándo usar:** Cuando despliegas en Render o cualquier servidor de producción.

## 🔄 **Cómo Cambiar de Entorno**

### **Paso 1: Editar config.js**
1. Abre `frontend/config.js`
2. Comenta la línea del entorno que NO quieres usar
3. Descomenta la línea del entorno que SÍ quieres usar

### **Paso 2: Ejemplo de Cambio**

**Antes (Desarrollo):**
```javascript
const BACKEND_URL = 'http://localhost:5000';
// const BACKEND_URL = 'https://proyecto-ocr-odoo-1.onrender.com';
```

**Después (Producción):**
```javascript
// const BACKEND_URL = 'http://localhost:5000';
const BACKEND_URL = 'https://proyecto-ocr-odoo-1.onrender.com';
```

## 🧪 **Verificación**

### **Desarrollo Local:**
1. Asegúrate de que `BACKEND_URL = 'http://localhost:5000'`
2. Ejecuta `python app.py` en el backend
3. Abre `http://localhost:5000` en tu navegador
4. Debería mostrar "✅ Backend OCR.Space conectado. Sistema OCR v3.0 listo."

### **Producción:**
1. Cambia a `BACKEND_URL = 'https://proyecto-ocr-odoo-1.onrender.com'`
2. Haz commit y push a tu repositorio
3. Render redeployará automáticamente
4. Prueba desde tu teléfono - debería funcionar

## 🚨 **Solución de Problemas**

### **Error: "No se pudo conectar con el servidor OCR"**

**Causas posibles:**
1. **URL incorrecta en config.js**
2. **Backend no ejecutándose**
3. **Puerto incorrecto**
4. **Problema de CORS**

**Soluciones:**
1. Verifica que `config.js` tenga la URL correcta
2. Asegúrate de que el backend esté ejecutándose
3. Verifica que el puerto sea 5000
4. Usa la página de prueba: `/test-connection`

### **Verificación Rápida:**
```bash
# Verificar que el backend esté ejecutándose
netstat -an | findstr :5000

# Probar la API directamente
curl http://localhost:5000/api/health
```

## 📱 **Páginas de Prueba**

- **Prueba de conexión:** `/test-connection`
- **Prueba de detección de URL:** `/test-url`
- **Health check:** `/api/health`

## 💡 **Tips**

- **Siempre verifica** que `config.js` tenga la URL correcta
- **Para desarrollo:** Usa `localhost:5000`
- **Para producción:** Usa la URL de tu servidor (ej: Render)
- **Si cambias de entorno:** Recarga la página del navegador
- **Mantén un backup** de las configuraciones que funcionan 