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

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Verificar e importar Tesseract
try:
    import pytesseract
    # Configurar path de Tesseract si es necesario (Windows)
    # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSERACT_AVAILABLE = True
    logger.info("✅ Tesseract disponible")
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("⚠️ Tesseract no disponible - se usará texto de prueba")

def preprocess_image_advanced(image, brightness=0, contrast=100, sharpness=0):
    """Preprocesamiento avanzado de imagen para OCR de máxima precisión"""
    try:
        # Convertir a RGB si es necesario
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logger.info(f"Imagen original: {image.size}, modo: {image.mode}")
        
        # Aplicar ajustes básicos
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
        
        # Convertir a array de OpenCV para procesamiento avanzado
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Reducción de ruido
        cv_image = cv2.bilateralFilter(cv_image, 9, 75, 75)
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Umbralización adaptativa para mejor contraste
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Operaciones morfológicas para limpiar la imagen
        kernel = np.ones((1, 1), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Convertir de vuelta a PIL
        processed_image = Image.fromarray(thresh)
        
        # Redimensionar si es muy pequeña (mínimo 300 DPI equivalente)
        if processed_image.width < 1000 or processed_image.height < 1000:
            scale_factor = max(1000 / processed_image.width, 1000 / processed_image.height)
            new_size = (
                int(processed_image.width * scale_factor),
                int(processed_image.height * scale_factor)
            )
            processed_image = processed_image.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Imagen redimensionada a: {new_size}")
        
        logger.info("✅ Preprocesamiento completado")
        return processed_image
        
    except Exception as e:
        logger.error(f"❌ Error en preprocesamiento: {e}")
        return image

def extract_text_with_multiple_configs(image):
    """Extraer texto usando múltiples configuraciones para máxima precisión"""
    if not TESSERACT_AVAILABLE:
        return {
            'text': 'Tesseract no disponible - Texto de ejemplo extraído de la imagen',
            'confidence': 85.0
        }
    
    # Configuraciones múltiples para diferentes tipos de texto
    configs = [
        {
            'name': 'Documento estándar',
            'config': '--oem 1 --psm 1 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,;:!?()[]{}"\'-/\\@#$%&*+=<>|~áéíóúüñÁÉÍÓÚÜÑ ',
            'lang': 'spa+eng'
        },
        {
            'name': 'Bloque de texto uniforme',
            'config': '--oem 1 --psm 6 -c preserve_interword_spaces=1',
            'lang': 'spa+eng'
        },
        {
            'name': 'Línea de texto única',
            'config': '--oem 1 --psm 7',
            'lang': 'spa+eng'
        },
        {
            'name': 'Palabra única',
            'config': '--oem 1 --psm 8',
            'lang': 'spa+eng'
        }
    ]
    
    best_result = None
    best_confidence = 0
    
    for config in configs:
        try:
            logger.info(f"Probando configuración: {config['name']}")
            
            # Extraer texto
            text = pytesseract.image_to_string(
                image, 
                config=config['config'],
                lang=config['lang']
            ).strip()
            
            # Calcular confianza
            try:
                data = pytesseract.image_to_data(
                    image,
                    config=config['config'],
                    lang=config['lang'],
                    output_type=pytesseract.Output.DICT
                )
                
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                confidence = sum(confidences) / len(confidences) if confidences else 0
                
            except Exception as conf_error:
                logger.warning(f"Error calculando confianza: {conf_error}")
                confidence = len(text) * 2  # Estimación basada en longitud de texto
            
            logger.info(f"Resultado: {len(text)} chars, {confidence:.1f}% confianza")
            
            # Seleccionar el mejor resultado
            if confidence > best_confidence and len(text) > 0:
                best_result = {
                    'text': text,
                    'confidence': confidence,
                    'config_used': config['name']
                }
                best_confidence = confidence
                
        except Exception as e:
            logger.warning(f"Error con configuración {config['name']}: {e}")
    
    if best_result:
        logger.info(f"✅ Mejor resultado: {best_result['config_used']} ({best_confidence:.1f}%)")
        return best_result
    else:
        logger.warning("❌ No se pudo extraer texto con ninguna configuración")
        return {
            'text': '',
            'confidence': 0,
            'config_used': 'Ninguna exitosa'
        }

def post_process_text(text):
    """Post-procesamiento inteligente del texto extraído"""
    if not text:
        return text
    
    original_length = len(text)
    
    # Eliminar líneas vacías múltiples
    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    
    # Corregir espacios múltiples
    import re
    text = re.sub(r'\s+', ' ', text)
    
    # Correcciones comunes de OCR (solo en contexto apropiado)
    corrections = {
        # Números confundidos con letras en contexto de letras
        r'\b([A-Za-záéíóúüñ]+)0([A-Za-záéíóúüñ]+)\b': r'\1O\2',
        r'\b([A-Za-záéíóúüñ]+)1([A-Za-záéíóúüñ]+)\b': r'\1I\2',
        r'\b([A-Za-záéíóúüñ]+)5([A-Za-záéíóúüñ]+)\b': r'\1S\2',
        r'\b([A-Za-záéíóúüñ]+)8([A-Za-záéíóúüñ]+)\b': r'\1B\2',
        
        # Caracteres especiales comunes
        r'\|': 'I',
        r'`': "'",
        r'´': "'",
        r''': "'",
        r''': "'",
        r'"': '"',
        r'"': '"',
        r'°': 'o',
        
        # Espacios antes de puntuación
        r'\s+([,.;:!?])': r'\1',
        
        # Espacios después de paréntesis de apertura
        r'\(\s+': '(',
        r'\s+\)': ')',
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
    """Procesar imagen con OCR de máxima precisión"""
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
        
        logger.info(f"🔄 Procesando OCR con parámetros: B:{brightness}, C:{contrast}, S:{sharpness}")
        
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
        
        # Preprocesar imagen
        preprocessing_start = time.time()
        processed_image = preprocess_image_advanced(image, brightness, contrast, sharpness)
        preprocessing_time = time.time() - preprocessing_start
        logger.info(f"⚡ Preprocesamiento completado en {preprocessing_time:.2f}s")
        
        # Extraer texto con múltiples configuraciones
        ocr_start = time.time()
        ocr_result = extract_text_with_multiple_configs(processed_image)
        ocr_time = time.time() - ocr_start
        logger.info(f"🔍 OCR completado en {ocr_time:.2f}s")
        
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
                'ocr_time': ocr_time,
                'postprocessing_time': postprocess_time,
                'config_used': ocr_result.get('config_used', 'Desconocida'),
                'characters_extracted': len(final_text),
                'tesseract_available': TESSERACT_AVAILABLE
            }
        }
        
        logger.info(f"🎯 OCR exitoso: {len(final_text)} chars, {ocr_result['confidence']:.1f}% confianza, {total_time:.2f}s total")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error general en process_ocr: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno del servidor: {str(e)}'
        }), 500

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """Probar conexión y capacidades del sistema"""
    try:
        # Verificar capacidades del sistema
        capabilities = {
            'tesseract_available': TESSERACT_AVAILABLE,
            'opencv_available': 'cv2' in globals(),
            'pil_available': True,  # Siempre disponible si llegamos aquí
            'server_time': datetime.now().isoformat(),
            'python_version': os.sys.version
        }
        
        if TESSERACT_AVAILABLE:
            try:
                tesseract_version = pytesseract.get_tesseract_version()
                capabilities['tesseract_version'] = str(tesseract_version)
                
                # Probar idiomas disponibles
                languages = pytesseract.get_languages()
                capabilities['available_languages'] = languages
                
            except Exception as tess_error:
                logger.warning(f"Error obteniendo info de Tesseract: {tess_error}")
                capabilities['tesseract_error'] = str(tess_error)
        
        logger.info("✅ Test de conexión exitoso")
        
        return jsonify({
            'success': True,
            'message': 'Conexión exitosa - Sistema OCR listo',
            'capabilities': capabilities
        })
        
    except Exception as e:
        logger.error(f"❌ Error en test_connection: {e}")
        return jsonify({
            'success': False,
            'message': f'Error del servidor: {str(e)}'
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
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'tesseract_available': TESSERACT_AVAILABLE
        })
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("🚀 Iniciando servidor OCR...")
    logger.info(f"Tesseract disponible: {TESSERACT_AVAILABLE}")
    app.run(debug=True, host='0.0.0.0', port=5000)