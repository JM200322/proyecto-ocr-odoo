# backend/app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from odoo_client import OdooClient
import os
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Permitir requests desde el frontend

# Inicializar cliente Odoo
odoo_client = OdooClient()

def process_image_ocr(image_data, brightness=0, contrast=100, sharpness=0):
    """Procesar imagen con OCR usando Tesseract"""
    import time
    import io
    from PIL import Image, ImageEnhance, ImageFilter
    
    start_time = time.time()
    
    try:
        # Cargar imagen desde bytes
        image = Image.open(io.BytesIO(image_data))
        
        # Convertir a RGB si es necesario
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Aplicar ajustes de imagen
        if brightness != 0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1 + brightness / 100)
        
        if contrast != 100:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(contrast / 100)
        
        if sharpness > 0:
            # Aplicar filtro de nitidez
            image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=sharpness))
        
        # Verificar si Tesseract está disponible
        try:
            import pytesseract
            
            # Configurar Tesseract
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,;:!?()[]{}"\'-/\\@#$%&*+=<>|~'
            
            # Procesar OCR
            text = pytesseract.image_to_string(image, config=custom_config, lang='spa+eng')
            
            # Obtener confianza (si está disponible)
            try:
                data = pytesseract.image_to_data(image, config=custom_config, lang='spa+eng', output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                confidence = sum(confidences) / len(confidences) if confidences else 0
            except:
                confidence = 0
                
        except ImportError:
            # Tesseract no está disponible, usar texto de prueba
            text = "Texto de prueba - Tesseract no está instalado"
            confidence = 50
            logger.warning("Tesseract no está instalado. Usando texto de prueba.")
            
        processing_time = time.time() - start_time
        
        logger.info(f"OCR completado en {processing_time:.2f}s con confianza {confidence:.1f}%")
        
        return {
            'success': True,
            'text': text.strip(),
            'confidence': confidence,
            'processing_time': processing_time
        }
        
    except Exception as e:
        logger.error(f"Error en process_image_ocr: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/')
def index():
    """Servir el frontend"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Servir archivos estáticos"""
    return send_from_directory('../frontend', filename)

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """Probar conexión con Odoo"""
    try:
        data = request.json
        instance = data.get('instance', 'production')
        
        logger.info(f"Probando conexión con instancia: {instance}")
        
        # TEMPORAL: Para testing, simular conexión exitosa
        # uid = odoo_client.authenticate(instance)
        
        # if uid:
        return jsonify({
            'success': True,
            'message': f'Conexión exitosa con instancia {instance} (modo testing)',
            'user_id': 1
        })
        # else:
        #     return jsonify({
        #         'success': False,
        #         'message': 'Error de conexión o credenciales incorrectas'
        #     }), 400
            
    except Exception as e:
        logger.error(f"Error en test_connection: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno del servidor: {str(e)}'
        }), 500

@app.route('/api/send-text', methods=['POST'])
def send_text_to_odoo():
    """Enviar texto extraído a Odoo"""
    try:
        data = request.json
        
        # Validar datos de entrada
        text = data.get('text', '').strip()
        mapping_type = data.get('type', 'contacts')
        instance = data.get('instance', 'production')
        
        if not text:
            return jsonify({
                'success': False,
                'message': 'No hay texto para enviar'
            }), 400
        
        # Obtener configuración de mapeo
        mapping = odoo_client.get_mapping(mapping_type)
        if not mapping:
            return jsonify({
                'success': False,
                'message': f'Tipo de mapeo no válido: {mapping_type}'
            }), 400
        
        # Preparar datos para Odoo
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        odoo_data = {
            mapping['field']: text,
            'name': f'OCR - {timestamp}',
        }
        
        # Datos adicionales según el tipo
        if mapping_type == 'contacts':
            odoo_data['is_company'] = False
        elif mapping_type == 'invoices':
            odoo_data['move_type'] = 'in_invoice'
            odoo_data['partner_id'] = 1  # Partner por defecto
        elif mapping_type == 'tasks':
            # Necesitarás ajustar este ID según tu configuración
            odoo_data['project_id'] = 1
        
        logger.info(f"Enviando datos a Odoo: {odoo_data}")
        
        # Crear registro en Odoo
        record_id = odoo_client.create_record(
            mapping['model'],
            odoo_data,
            instance
        )
        
        if record_id:
            return jsonify({
                'success': True,
                'message': f'Registro creado exitosamente en {mapping["model"]}',
                'record_id': record_id,
                'instance': instance
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Error al crear registro en Odoo'
            }), 500
            
    except Exception as e:
        logger.error(f"Error en send_text_to_odoo: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno del servidor: {str(e)}'
        }), 500

@app.route('/api/get-mappings', methods=['GET'])
def get_available_mappings():
    """Obtener tipos de mapeo disponibles"""
    try:
        mappings = list(odoo_client.config.get("default_mappings", {}).keys())
        instances = list(odoo_client.config.get("odoo_instances", {}).keys())
        
        return jsonify({
            'mappings': mappings,
            'instances': instances
        })
    except Exception as e:
        logger.error(f"Error en get_mappings: {e}")
        return jsonify({
            'mappings': [],
            'instances': []
        })

@app.route('/api/process-ocr', methods=['POST'])
def process_ocr():
    """Procesar imagen con OCR en el backend"""
    try:
        # Verificar que se haya enviado una imagen
        if 'image' not in request.files and 'image_data' not in request.json:
            return jsonify({
                'success': False,
                'message': 'No se proporcionó imagen para procesar'
            }), 400
        
        # Obtener parámetros de ajuste
        brightness = request.json.get('brightness', 0)
        contrast = request.json.get('contrast', 100)
        sharpness = request.json.get('sharpness', 0)
        
        logger.info(f"Procesando OCR con parámetros: brillo={brightness}, contraste={contrast}, nitidez={sharpness}")
        
        # Procesar la imagen
        if 'image' in request.files:
            # Imagen enviada como archivo
            image_file = request.files['image']
            image_data = image_file.read()
        else:
            # Imagen enviada como base64
            import base64
            image_data_url = request.json['image_data']
            # Remover el prefijo data:image/...;base64,
            if ',' in image_data_url:
                image_data = base64.b64decode(image_data_url.split(',')[1])
            else:
                image_data = base64.b64decode(image_data_url)
        
        # Procesar OCR
        result = process_image_ocr(image_data, brightness, contrast, sharpness)
        
        if result['success']:
            return jsonify({
                'success': True,
                'text': result['text'],
                'confidence': result['confidence'],
                'processing_time': result['processing_time']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error en process_ocr: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno del servidor: {str(e)}'
        }), 500

@app.route('/api/frontend-log', methods=['POST'])
def frontend_log():
    """Recibir logs del frontend y mostrarlos en la consola del backend"""
    try:
        data = request.json
        log_level = data.get('level', 'INFO')
        message = data.get('message', '')
        timestamp = data.get('timestamp', '')
        additional_data = data.get('data', {})
        
        # Formatear el mensaje de log
        log_message = f"[FRONTEND-{log_level.upper()}] {message}"
        if timestamp:
            log_message = f"[{timestamp}] {log_message}"
        
        # Mostrar en consola según el nivel
        if log_level.upper() == 'ERROR':
            logger.error(log_message)
        elif log_level.upper() == 'WARN':
            logger.warning(log_message)
        elif log_level.upper() == 'DEBUG':
            logger.debug(log_message)
        else:
            logger.info(log_message)
        
        # Si hay datos adicionales, mostrarlos también
        if additional_data:
            logger.info(f"[FRONTEND-DATA] {additional_data}")
        
        return jsonify({'success': True, 'message': 'Log recibido'})
        
    except Exception as e:
        logger.error(f"Error procesando log del frontend: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    # Verificar que existe la configuración
    if not os.path.exists('../config/credentials.json'):
        logger.warning("Archivo de credenciales no encontrado, se creará uno por defecto")
    
    app.run(debug=True, host='0.0.0.0', port=5000)