# backend/app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import time
import base64
import io
import logging
from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import cv2
import numpy as np
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuración OCR.Space - USAR VARIABLE DE ENTORNO EN PRODUCCIÓN
OCR_SPACE_API_KEY = os.environ.get('OCR_SPACE_API_KEY', 'K86759595888957')
OCR_SPACE_ENDPOINT = "https://api.ocr.space/parse/image"

# Detectar si estamos en Render
IS_RENDER = os.environ.get('RENDER') == 'true' or os.environ.get('RENDER_SERVICE_NAME') is not None

# Configuración específica para Render
if IS_RENDER:
    # Timeouts más largos para Render
    DEFAULT_TIMEOUT = 120  # 2 minutos
    MAX_RETRIES = 5
    logger.info("🚀 Ejecutando en Render - Configuración de producción activada")
else:
    # Configuración local
    DEFAULT_TIMEOUT = 60
    MAX_RETRIES = 3
    logger.info("💻 Ejecutando localmente - Configuración de desarrollo")

logger.info(f"✅ Servidor OCR inicializado")
logger.info(f"API Key configurada: {'Sí' if OCR_SPACE_API_KEY else 'No'}")
logger.info(f"Entorno: {'Render' if IS_RENDER else 'Local'}")

def load_and_prepare_image(image: Image.Image, max_px: int = 2200, target_size_kb: int = 900) -> bytes:
    """Prepara imagen optimizada para OCR.Space"""
    try:
        # Asegurar que la imagen esté cargada completamente
        image.load()
        
        # Convertir a RGB (evita CMYK/alpha)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
            logger.info(f"Imagen convertida a RGB desde modo: {image.mode}")
        
        # Escala si el lado largo excede max_px
        w, h = image.size
        m = max(w, h)
        if m > max_px:
            scale = max_px / float(m)
            new_size = (int(w * scale), int(h * scale))
            image = image.resize(new_size, Image.LANCZOS)
            logger.info(f"Imagen redimensionada de {w}x{h} a {new_size[0]}x{new_size[1]}")
        
        # Preprocesado suave: grises + contraste + sharpen
        grayscale = ImageOps.grayscale(image)
        grayscale = ImageOps.autocontrast(grayscale)
        grayscale = grayscale.filter(ImageFilter.SHARPEN)
        logger.info("Aplicado preprocesamiento: escala de grises + autocontraste + sharpen")
        
        # Guardar a JPEG optimizado intentando < target_size_kb
        for quality in (90, 85, 80, 75, 70):
            buf = io.BytesIO()
            grayscale.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
            size_kb = buf.tell() / 1024
            if size_kb <= target_size_kb:
                logger.info(f"Imagen comprimida a JPEG con calidad {quality}, tamaño: {size_kb:.1f}KB")
                buf.seek(0)
                return buf.getvalue()
        
        # Fallback a PNG optimizado si JPEG no funciona
        buf = io.BytesIO()
        grayscale.save(buf, format="PNG", optimize=True)
        size_kb = buf.tell() / 1024
        logger.info(f"Fallback a PNG, tamaño: {size_kb:.1f}KB")
        buf.seek(0)
        return buf.getvalue()
        
    except Exception as e:
        logger.error(f"Error preparando imagen: {e}")
        raise

def preprocess_image_advanced(image: Image.Image, brightness: int = 0, contrast: int = 100, sharpness: int = 0) -> Image.Image:
    """Preprocesamiento adicional basado en parámetros del usuario"""
    try:
        # Convertir a RGB si es necesario
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Aplicar ajustes del usuario
        if brightness != 0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1 + brightness / 100)
            logger.info(f"Brillo ajustado: {brightness}")
        
        if contrast != 100:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(contrast / 100)
            logger.info(f"Contraste ajustado: {contrast}%")
        
        if sharpness > 0:
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1 + sharpness / 100)
            logger.info(f"Nitidez aplicada: {sharpness}")
        
        # Procesamiento adicional con OpenCV si está disponible
        try:
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Reducción de ruido
            cv_image = cv2.bilateralFilter(cv_image, 9, 75, 75)
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Umbralización adaptativa
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Operaciones morfológicas
            kernel = np.ones((1, 1), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            # Convertir de vuelta a PIL
            processed_image = Image.fromarray(thresh)
            logger.info("Procesamiento OpenCV aplicado exitosamente")
            return processed_image
            
        except Exception as cv_error:
            logger.warning(f"OpenCV no disponible o error: {cv_error}. Usando imagen con ajustes básicos.")
            return image
        
    except Exception as e:
        logger.error(f"Error en preprocesamiento avanzado: {e}")
        return image

def test_ocr_connection() -> Dict[str, Any]:
    """Prueba rápida de conexión con OCR.Space"""
    try:
        logger.info("Probando conexión con OCR.Space...")
        
        # Crear una imagen de prueba mínima
        test_img = Image.new('RGB', (100, 50), color='white')
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(test_img)
        
        # Escribir texto de prueba
        try:
            # Intentar usar una fuente por defecto
            draw.text((10, 15), "TEST", fill='black')
        except:
            pass
        
        # Preparar imagen
        buf = io.BytesIO()
        test_img.save(buf, format="JPEG", quality=90)
        buf.seek(0)
        image_bytes = buf.getvalue()
        
        # Hacer petición de prueba con timeout corto
        data = {
            "apikey": OCR_SPACE_API_KEY,
            "language": "eng",
            "isOverlayRequired": False,
            "OCREngine": 1,  # Engine 1 es más rápido para pruebas
        }
        
        response = requests.post(
            OCR_SPACE_ENDPOINT,
            data=data,
            files={"filename": ("test.jpg", image_bytes, "application/octet-stream")},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if not result.get("IsErroredOnProcessing", True):
                logger.info("✅ Conexión con OCR.Space exitosa")
                return {"success": True, "message": "Conexión exitosa"}
            else:
                error_msg = result.get("ErrorMessage", "Error desconocido")
                logger.error(f"❌ Error de OCR.Space: {error_msg}")
                return {"success": False, "message": f"Error API: {error_msg}"}
        else:
            logger.error(f"❌ HTTP {response.status_code}: {response.text[:200]}")
            return {"success": False, "message": f"HTTP {response.status_code}"}
            
    except requests.Timeout:
        logger.error("❌ Timeout al conectar con OCR.Space")
        return {"success": False, "message": "Timeout - La API no responde"}
    except requests.ConnectionError as e:
        logger.error(f"❌ Error de conexión: {e}")
        return {"success": False, "message": "No se puede conectar con OCR.Space"}
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return {"success": False, "message": str(e)}

def ocr_space_image(image_bytes: bytes, language: str = "spa", engine: int = 2, retries: int = None, timeout: int = None) -> Dict[str, Any]:
    """Llama OCR.Space con reintentos exponenciales y manejo robusto de errores"""
    
    # Usar configuración según entorno
    if retries is None:
        retries = MAX_RETRIES
    if timeout is None:
        timeout = DEFAULT_TIMEOUT
    
    # En Render, primero hacer una prueba de conexión
    if IS_RENDER and retries == MAX_RETRIES:  # Solo en el primer intento
        conn_test = test_ocr_connection()
        if not conn_test["success"]:
            logger.error(f"Fallo prueba de conexión: {conn_test['message']}")
            # Continuar de todos modos, por si acaso
    
    data = {
        "apikey": OCR_SPACE_API_KEY,
        "language": language,
        "isOverlayRequired": False,
        "OCREngine": engine,
        "detectOrientation": True,
        "scale": True,
    }
    
    # Headers adicionales para Render
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    backoff = 2 if not IS_RENDER else 3  # Mayor backoff en Render
    last_error = None
    
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Intento {attempt}/{retries} de OCR.Space con engine={engine}, timeout={timeout}s")
            
            # Hacer la petición
            response = requests.post(
                OCR_SPACE_ENDPOINT,
                data=data,
                files={"filename": ("image.jpg", image_bytes, "application/octet-stream")},
                headers=headers,
                timeout=timeout,
            )
            
            logger.info(f"Respuesta HTTP: {response.status_code}")
            
            # Verificar respuesta HTTP
            if response.status_code != 200:
                logger.error(f"Error HTTP {response.status_code}: {response.text[:500]}")
                if response.status_code == 403:
                    return {
                        'text': '',
                        'confidence': 0,
                        'success': False,
                        'message': 'API Key inválida o límite excedido'
                    }
                raise requests.HTTPError(f"HTTP {response.status_code}")
            
            payload = response.json()
            
            # Log detallado en Render
            if IS_RENDER:
                logger.info(f"Respuesta JSON keys: {list(payload.keys())}")
            
            # Manejo de errores de la API
            if payload.get("IsErroredOnProcessing"):
                error_msg = payload.get("ErrorMessage") or payload.get("ErrorDetails") or "Unknown error"
                logger.error(f"OCR.Space error: {error_msg}")
                
                # Si es error de engine, intentar con otro
                if "OCREngine" in error_msg and engine == 2:
                    logger.info("Reintentando con OCREngine=3")
                    return ocr_space_image(image_bytes, language, engine=3, retries=2, timeout=timeout)
                elif "OCREngine" in error_msg and engine == 3:
                    logger.info("Reintentando con OCREngine=1")
                    return ocr_space_image(image_bytes, language, engine=1, retries=2, timeout=timeout)
                
                # Si es error de límite de API
                if "limit" in error_msg.lower() or "quota" in error_msg.lower():
                    return {
                        'text': '',
                        'confidence': 0,
                        'success': False,
                        'message': 'Límite de API excedido. Intenta más tarde.'
                    }
                
                raise RuntimeError(f"OCR.Space API error: {error_msg}")
            
            # Procesar resultados
            results = payload.get("ParsedResults") or []
            if not results:
                logger.warning("No se obtuvieron resultados de OCR")
                return {
                    'text': '',
                    'confidence': 0,
                    'success': False,
                    'message': 'No se detectó texto en la imagen'
                }
            
            # Extraer texto
            parsed_result = results[0]
            text = parsed_result.get("ParsedText", "")
            
            # Calcular confianza
            confidence = 100.0 if text.strip() else 0.0
            if text:
                special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
                confidence = max(50, 100 - (special_chars * 2))
            
            logger.info(f"✅ OCR exitoso: {len(text)} caracteres extraídos")
            
            return {
                'text': text,
                'confidence': confidence,
                'success': True,
                'engine_used': engine,
                'processing_time': response.elapsed.total_seconds()
            }
            
        except requests.Timeout:
            last_error = "Timeout"
            logger.warning(f"Timeout en intento {attempt}")
            
            if attempt < retries:
                sleep_time = backoff
                logger.info(f"Esperando {sleep_time}s antes de reintentar...")
                time.sleep(sleep_time)
                backoff *= 2
                # Aumentar timeout para siguiente intento
                timeout = min(timeout * 1.5, 180)  # Max 3 minutos
            
        except (requests.ConnectionError, requests.HTTPError) as e:
            last_error = str(e)
            logger.warning(f"Error de conexión en intento {attempt}: {e}")
            
            if attempt < retries:
                sleep_time = backoff
                logger.info(f"Esperando {sleep_time}s antes de reintentar...")
                time.sleep(sleep_time)
                backoff *= 2
                
        except Exception as e:
            last_error = str(e)
            logger.error(f"Error inesperado: {e}")
            # En errores inesperados, intentar con otro engine
            if attempt == 1 and engine == 2:
                logger.info("Error inesperado, probando con engine 1")
                return ocr_space_image(image_bytes, language, engine=1, retries=2, timeout=timeout)
            break
    
    # Si llegamos aquí, todos los intentos fallaron
    return {
        'text': '',
        'confidence': 0,
        'success': False,
        'message': f'Error después de {retries} intentos: {last_error}'
    }

def post_process_text(text: str) -> str:
    """Post-procesamiento inteligente del texto extraído"""
    if not text:
        return text
    
    original_length = len(text)
    
    # Eliminar líneas vacías múltiples
    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    
    # Corregir espacios múltiples
    import re
    text = re.sub(r'\s+', ' ', text)
    
    # Correcciones comunes de OCR
    corrections = {
        # Espacios antes de puntuación
        r'\s+([,.;:!?])': r'\1',
        # Espacios después de paréntesis
        r'\(\s+': '(',
        r'\s+\)': ')',
        # Comillas tipográficas a normales
        r'[''´`]': "'",
        r'["""]': '"',
    }
    
    for pattern, replacement in corrections.items():
        text = re.sub(pattern, replacement, text)
    
    # Limpiar espacios al inicio y final
    text = text.strip()
    
    logger.info(f"Post-procesamiento: {original_length} -> {len(text)} caracteres")
    
    return text

@app.route('/')
def index():
    """Servir el frontend"""
    try:
        return send_from_directory('../frontend', 'index.html')
    except Exception as e:
        return f"Error sirviendo frontend: {e}", 500

@app.route('/static/<path:filename>')
def static_files(filename):
    """Servir archivos estáticos del frontend"""
    try:
        return send_from_directory('../frontend', filename)
    except Exception as e:
        return f"Error sirviendo archivo estático: {e}", 404

@app.route('/api/process-ocr', methods=['POST'])
def process_ocr():
    """Procesar imagen con OCR optimizado"""
    start_time = time.time()
    
    try:
        data = request.json
        if not data or 'image_data' not in data:
            return jsonify({
                'success': False,
                'message': 'No se proporcionó imagen'
            }), 400
        
        # Obtener parámetros
        brightness = data.get('brightness', 0)
        contrast = data.get('contrast', 100)
        sharpness = data.get('sharpness', 0)
        engine = data.get('engine', 2)
        
        logger.info(f"🔄 Procesando OCR con parámetros: B:{brightness}, C:{contrast}, S:{sharpness}, Engine:{engine}")
        logger.info(f"Entorno: {'Render' if IS_RENDER else 'Local'}")
        
        # Decodificar imagen base64
        try:
            image_data_url = data['image_data']
            if ',' in image_data_url:
                image_data = base64.b64decode(image_data_url.split(',')[1])
            else:
                image_data = base64.b64decode(image_data_url)
            
            # Cargar imagen
            image = Image.open(io.BytesIO(image_data))
            logger.info(f"✅ Imagen cargada: {image.size}")
            
        except Exception as img_error:
            logger.error(f"❌ Error decodificando imagen: {img_error}")
            return jsonify({
                'success': False,
                'message': f'Error al procesar imagen: {img_error}'
            }), 400
        
        # Aplicar preprocesamiento del usuario si hay ajustes
        preprocessing_start = time.time()
        if brightness != 0 or contrast != 100 or sharpness != 0:
            image = preprocess_image_advanced(image, brightness, contrast, sharpness)
        preprocessing_time = time.time() - preprocessing_start
        
        # Preparar imagen optimizada para OCR.Space
        prepare_start = time.time()
        image_bytes = load_and_prepare_image(image)
        prepare_time = time.time() - prepare_start
        logger.info(f"⚡ Preparación de imagen completada en {prepare_time:.2f}s")
        
        # Extraer texto con OCR.Space
        ocr_start = time.time()
        ocr_result = ocr_space_image(image_bytes, language="spa", engine=engine)
        ocr_time = time.time() - ocr_start
        logger.info(f"🔍 OCR completado en {ocr_time:.2f}s")
        
        if not ocr_result['success']:
            logger.warning(f"OCR falló: {ocr_result.get('message', 'Sin mensaje')}")
            return jsonify({
                'success': False,
                'message': ocr_result.get('message', 'Error en el procesamiento OCR'),
                'details': {
                    'preprocessing_time': preprocessing_time,
                    'prepare_time': prepare_time,
                    'ocr_time': ocr_time,
                    'environment': 'render' if IS_RENDER else 'local'
                }
            }), 500
        
        # Post-procesar texto
        postprocess_start = time.time()
        final_text = post_process_text(ocr_result['text'])
        postprocess_time = time.time() - postprocess_start
        logger.info(f"✨ Post-procesamiento completado en {postprocess_time:.2f}s")
        
        total_time = time.time() - start_time
        
        # Preparar respuesta
        response = {
            'success': True,
            'text': final_text,
            'confidence': ocr_result['confidence'],
            'processing_time': total_time,
            'details': {
                'preprocessing_time': preprocessing_time,
                'prepare_time': prepare_time,
                'ocr_time': ocr_time,
                'postprocessing_time': postprocess_time,
                'engine_used': ocr_result.get('engine_used', engine),
                'characters_extracted': len(final_text),
                'ocr_space_available': True,
                'environment': 'render' if IS_RENDER else 'local'
            }
        }
        
        logger.info(f"🎯 OCR exitoso: {len(final_text)} chars, {ocr_result['confidence']:.1f}% confianza, {total_time:.2f}s total")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error general en process_ocr: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno del servidor: {str(e)}',
            'environment': 'render' if IS_RENDER else 'local'
        }), 500

@app.route('/api/test-connection', methods=['POST', 'GET'])
def test_connection():
    """Probar conexión y capacidades del sistema"""
    try:
        logger.info("🔍 Iniciando test de conexión...")
        
        # Verificar capacidades del sistema
        capabilities = {
            'ocr_space_available': True,
            'opencv_available': 'cv2' in globals(),
            'pil_available': True,
            'server_time': datetime.now().isoformat(),
            'python_version': os.sys.version,
            'ocr_api_key': OCR_SPACE_API_KEY[:8] + '...' if OCR_SPACE_API_KEY else 'No configurado',
            'ocr_endpoint': OCR_SPACE_ENDPOINT,
            'environment': 'render' if IS_RENDER else 'local',
            'render_service': os.environ.get('RENDER_SERVICE_NAME', 'N/A'),
            'timeout_config': DEFAULT_TIMEOUT,
            'max_retries': MAX_RETRIES
        }
        
        # Probar conexión con OCR.Space
        ocr_test = test_ocr_connection()
        capabilities['ocr_space_test'] = ocr_test['success']
        capabilities['ocr_space_message'] = ocr_test['message']
        
        logger.info(f"✅ Test de conexión completado: {ocr_test['message']}")
        
        return jsonify({
            'success': True,
            'message': 'Sistema OCR listo' if ocr_test['success'] else f"Advertencia: {ocr_test['message']}",
            'capabilities': capabilities
        })
        
    except Exception as e:
        logger.error(f"❌ Error en test_connection: {e}")
        return jsonify({
            'success': False,
            'message': f'Error del servidor: {str(e)}',
            'environment': 'render' if IS_RENDER else 'local'
        }), 500

@app.route('/api/frontend-log', methods=['POST'])
def frontend_log():
    """Recibir y procesar logs del frontend"""
    try:
        data = request.json
        log_level = data.get('level', 'INFO').upper()
        message = data.get('message', '')
        timestamp = data.get('timestamp', '')
        additional_data = data.get('data', {})
        
        # Formatear mensaje
        log_message = f"[FRONTEND-{log_level}] {message}"
        if timestamp:
            log_message = f"[{timestamp}] {log_message}"
        
        # Log según nivel
        if log_level == 'ERROR':
            logger.error(log_message)
        elif log_level == 'WARN':
            logger.warning(log_message)
        elif log_level == 'DEBUG':
            logger.debug(log_message)
        else:
            logger.info(log_message)
        
        # Datos adicionales
        if additional_data:
            logger.info(f"[FRONTEND-DATA] {additional_data}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error procesando log del frontend: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificar estado del servidor"""
    try:
        # Hacer prueba rápida de OCR si estamos en Render
        ocr_status = "not_tested"
        if IS_RENDER:
            test_result = test_ocr_connection()
            ocr_status = "healthy" if test_result["success"] else "unhealthy"
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'ocr_space_available': True,
            'ocr_api_key_configured': bool(OCR_SPACE_API_KEY),
            'ocr_status': ocr_status,
            'environment': 'render' if IS_RENDER else 'local',
            'endpoint': OCR_SPACE_ENDPOINT
        })
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'environment': 'render' if IS_RENDER else 'local'
        }), 500

if __name__ == '__main__':
    logger.info("🚀 Iniciando servidor OCR optimizado...")
    logger.info(f"Configuración:")
    logger.info(f"  - Entorno: {'Render' if IS_RENDER else 'Local'}")
    logger.info(f"  - API Key: {'Configurada' if OCR_SPACE_API_KEY else 'NO CONFIGURADA'}")
    logger.info(f"  - Endpoint: {OCR_SPACE_ENDPOINT}")
    logger.info(f"  - Timeout: {DEFAULT_TIMEOUT}s")
    logger.info(f"  - Max reintentos: {MAX_RETRIES}")
    
    # Hacer prueba inicial de conexión
    logger.info("Realizando prueba inicial de conexión...")
    test_result = test_ocr_connection()
    if test_result["success"]:
        logger.info("✅ Conexión inicial con OCR.Space exitosa")
    else:
        logger.warning(f"⚠️ Problema con conexión inicial: {test_result['message']}")
    
    # Puerto de Render o 5000 local
    port = int(os.environ.get('PORT', 5000))
    
    app.run(
        debug=not IS_RENDER,  # Debug solo en local
        host='0.0.0.0',
        port=port
    )