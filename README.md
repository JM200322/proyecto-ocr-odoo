# OCR → Odoo Tool

Herramienta para escanear documentos con OCR y enviar el texto extraído a Odoo.

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
- Navegador moderno (Chrome, Firefox, Safari)
- Odoo instalado y funcionando

### Backend
```bash
cd backend
pip install -r requirements.txt
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
- Procesamiento OCR con Tesseract.js
- Múltiples idiomas (español, inglés)
- Fallback automático si un idioma falla

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
3. **Revisar texto:** El texto extraído aparecerá en el área de texto
4. **Enviar a Odoo:** Haz clic en "📤 Enviar a Odoo" o presiona Ctrl+Enter

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