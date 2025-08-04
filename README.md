# OCR → Odoo Tool

Herramienta para escanear documentos con OCR y enviar el texto extraído a Odoo.

## 🆕 Nuevas Características (v2.0)

### OCR en Backend
- **Procesamiento OCR en el servidor** para mayor precisión
- **Tesseract nativo** en lugar de Tesseract.js
- **Ajustes de imagen en tiempo real** (brillo, contraste, nitidez)
- **Mejor rendimiento** y confiabilidad

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
- Tesseract OCR
- Navegador moderno (Chrome, Firefox, Safari)
- Odoo instalado y funcionando

### Instalación Automática
```bash
cd backend
python install_dependencies.py
```

### Instalación Manual
```bash
cd backend
pip install -r requirements.txt

# Instalar Tesseract OCR:
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

### Ejecutar
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
- **Procesamiento OCR en el servidor** con Tesseract nativo
- **Ajustes de imagen en tiempo real** (brillo, contraste, nitidez)
- Múltiples idiomas (español, inglés)
- **Mayor precisión** y confiabilidad

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