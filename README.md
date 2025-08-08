# OCR → Odoo Tool

Herramienta para escanear documentos con OCR y enviar el texto extraído a Odoo.

## 🆕 Nuevas Características (v3.0) - OCR.Space API

### OCR Mejorado con OCR.Space
- **API OCR.Space** para máxima precisión y confiabilidad
- **Procesamiento optimizado** con preprocesamiento avanzado
- **Múltiples motores OCR** (engine 1, 2, 3) para diferentes tipos de documentos
- **Mejor rendimiento** y estabilidad que Tesseract local
- **Sin dependencias locales** de Tesseract

### Mejoras en la Interfaz
- **Controles de ajuste de imagen** antes del OCR
- **Vista previa en tiempo real** de los ajustes
- **Procesamiento más preciso** con parámetros optimizables
- **Mejor experiencia de usuario** con feedback visual

## 🚨 Problemas Identificados y Solucionados

### 1. **Error en OCR: "Error desconocido"**
**Problema:** El error "Error desconocido" ocurría debido a un manejo de errores incompleto en el proceso de OCR.

**Solución implementada:**
- Mejorado el manejo de errores en `processOCR()` y `testOCR()`
- Agregada validación de resultados del OCR
- Implementado manejo específico de errores de reconocimiento
- Agregado debugging detallado para identificar problemas

### 2. **Archivo de configuración faltante**
**Problema:** No existía el archivo `config/credentials.json` necesario para conectar con Odoo.

**Solución implementada:**
- Creado archivo `config/credentials.json` con configuración por defecto
- Configuración apunta a `localhost:8069` (puerto estándar de Odoo)
- Credenciales por defecto: admin/admin

### 3. **Dependencias faltantes en el backend**
**Problema:** El archivo `requirements.txt` no incluía todas las dependencias necesarias.

**Solución implementada:**
- Agregada dependencia `xmlrpc` para conexión con Odoo
- Verificadas todas las dependencias necesarias

### 4. **Manejo de errores de red**
**Problema:** No había verificación de conectividad de red para Tesseract.js.

**Solución implementada:**
- Agregada función `checkNetworkConnectivity()`
- Mejorada verificación de carga de Tesseract.js
- Agregado timeout en conexiones al backend

## 🛠️ Instalación y Configuración

### Requisitos
- Python 3.7+
- API Key de OCR.Space (gratuita hasta 500 requests/día)
- Navegador moderno (Chrome, Firefox, Safari)
- Odoo instalado y funcionando

### Instalación Automática
```bash
cd backend
python install_dependencies.py
python setup_ocr_space.py  # Configurar API key de OCR.Space
```

### Instalación Manual
```bash
cd backend
pip install -r requirements.txt

# Configurar API Key de OCR.Space:
# 1. Ve a https://ocr.space/ocrapi
# 2. Regístrate para obtener una API key gratuita
# 3. Edita backend/ocr_space_client.py y cambia la API_KEY
```

### Ejecutar

**Opción 1 - Script de inicio rápido (recomendado):**
```bash
python start_server.py
```

**Opción 2 - Inicio manual:**
```bash
cd backend
python app.py
```

### Frontend
Abrir `frontend/index.html` en el navegador o usar el servidor Flask:
```
http://localhost:5000
```

## ⚙️ Configuración

### 1. Configurar Odoo
Editar `config/credentials.json`:
```json
{
    "odoo_instances": {
        "production": {
            "url": "http://tu-servidor-odoo:8069",
            "database": "tu_base_de_datos",
            "username": "tu_usuario",
            "password": "tu_contraseña"
        }
    }
}
```

### 2. Configurar Backend
El backend se ejecuta en `http://localhost:5000` por defecto.

## 🔧 Funcionalidades

### OCR
- Captura de imágenes con cámara
- **Procesamiento OCR con OCR.Space API** para máxima precisión
- **Preprocesamiento avanzado** de imágenes (escala de grises, contraste, nitidez)
- **Múltiples motores OCR** (engine 1, 2, 3) para diferentes tipos de documentos
- Múltiples idiomas (español, inglés)
- **Mayor precisión** y confiabilidad que Tesseract local

### Debugging
- Modo debug activable con Ctrl+D
- Logs detallados en consola
- Información de estado del sistema
- Pruebas de conectividad

### Integración con Odoo
- Creación de contactos
- Creación de facturas
- Creación de tareas
- Mapeo configurable de campos

## 🎯 Uso

1. **Iniciar cámara:** Haz clic en "📷 Iniciar Cámara"
2. **Capturar documento:** Presiona Espacio o haz clic en "📸 Capturar"
3. **Ajustar imagen:** Usa los controles de brillo, contraste y nitidez
4. **Procesar OCR:** Haz clic en "Aplicar y Procesar"
5. **Revisar texto:** El texto extraído aparecerá en el área de texto
6. **Enviar a Odoo:** Haz clic en "📤 Enviar a Odoo" o presiona Ctrl+Enter

## ⌨️ Atajos de Teclado

- **Espacio:** Capturar foto
- **Ctrl + Enter:** Enviar a Odoo
- **Escape:** Volver a tomar foto
- **Ctrl + D:** Modo debug

## 🐛 Solución de Problemas

### Error de OCR
1. Activa el modo debug (Ctrl+D)
2. Revisa la consola del navegador
3. Usa el botón "🧪 Probar OCR"
4. Si persiste, usa "🔄 Reiniciar OCR"

### Error de Cámara
1. Verifica permisos del navegador
2. Asegúrate de usar HTTPS o localhost
3. Cierra otras apps que usen la cámara
4. Usa Chrome, Firefox o Safari actualizado

### Error de Conexión
1. Verifica que el backend esté ejecutándose
2. Revisa la URL del backend en configuración
3. Verifica credenciales de Odoo
4. Revisa logs del backend

## 📊 Estadísticas

La aplicación muestra estadísticas en tiempo real:
- Documentos procesados
- Documentos enviados
- Confianza promedio del OCR

## 🔒 Seguridad

- Las credenciales se almacenan localmente
- No se envían datos sensibles al frontend
- Conexiones HTTPS recomendadas para producción 