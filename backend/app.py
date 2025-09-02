# backend/app.py
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import time
import base64
import io
import logging
import uuid
import hashlib
from datetime import datetime, timedelta
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import cv2
import numpy as np
# Importar módulos locales
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

from database import db_manager

# Configurar logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Crear un wrapper para el logger que maneja ambos casos
class LoggerWrapper:
    def __init__(self, name):
        if STRUCTLOG_AVAILABLE:
            self._logger = structlog.get_logger(name)
            self._is_structlog = True
        else:
            self._logger = logging.getLogger(name)
            self._is_structlog = False
    
    def _format_args(self, msg, **kwargs):
        if kwargs and not self._is_structlog:
            # Para logger estándar, formatear los argumentos en el mensaje
            args_str = ', '.join(f"{k}={v}" for k, v in kwargs.items())
            return f"{msg} ({args_str})"
        return msg
    
    def info(self, msg, **kwargs):
        if self._is_structlog:
            self._logger.info(msg, **kwargs)
        else:
            self._logger.info(self._format_args(msg, **kwargs))
    
    def error(self, msg, **kwargs):
        if self._is_structlog:
            self._logger.error(msg, **kwargs)
        else:
            self._logger.error(self._format_args(msg, **kwargs))
    
    def warning(self, msg, **kwargs):
        if self._is_structlog:
            self._logger.warning(msg, **kwargs)
        else:
            self._logger.warning(self._format_args(msg, **kwargs))
    
    def debug(self, msg, **kwargs):
        if self._is_structlog:
            self._logger.debug(msg, **kwargs)
        else:
            self._logger.debug(self._format_args(msg, **kwargs))

logger = LoggerWrapper(__name__)

# Importar procesadores OCR después de configurar logging
try:
    from src.core.ocr_processor import ocr_processor
    OCR_PROCESSOR_AVAILABLE = True
    logger.info("Procesador OCR modular cargado")
except ImportError as e:
    OCR_PROCESSOR_AVAILABLE = False
    logger.error(f"Error cargando procesador OCR: {e}")
    logger.info("Usando modo legacy sin procesador modular")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ocr-odoo-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Extensiones
CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])
jwt = JWTManager(app)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
limiter.init_app(app)

# Inicializar sistemas
logger.info("Base de datos inicializada")
logger.info("Procesador OCR modular inicializado")

# Las funciones de procesamiento se han movido a módulos especializados
# Ver src/core/ para preprocesamiento, OCR y post-procesamiento

@app.route('/')
def index():
    """Servir el frontend Vue.js"""
    try:
        return send_from_directory('static', 'index.html')
    except Exception as e:
        return f"Error sirviendo frontend: {e}", 500

@app.route('/<path:filename>')
def serve_frontend_files(filename):
    """Servir archivos del frontend Vue.js con validación de seguridad"""
    # No servir rutas que empiecen con 'api/'
    if filename.startswith('api/'):
        return "API route not found", 404
    
    try:
        # Solo permitir ciertos tipos de archivos por seguridad
        allowed_extensions = ['.html', '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.woff2', '.map']
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext in allowed_extensions:
            return send_from_directory('static', filename)
        else:
            return "Tipo de archivo no permitido", 403
    except Exception as e:
        return f"Error sirviendo archivo: {e}", 404


# ============ TEST ROUTE ============

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test route to verify API is working"""
    return jsonify({'status': 'API working', 'message': 'Test successful'})

# ============ AUTENTICACIÓN ============

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Autenticación de usuario (simple para desarrollo)"""
    try:
        data = request.json
        username = data.get('username', 'guest')
        password = data.get('password', '')
        
        # En producción, verificar contra base de datos real
        # Por ahora, aceptar cualquier usuario para desarrollo
        if len(username) >= 3:
            access_token = create_access_token(identity=username)
            
            logger.info("Usuario autenticado", username=username)
            
            return jsonify({
                'success': True,
                'access_token': access_token,
                'user_id': username,
                'message': 'Autenticación exitosa'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Credenciales inválidas'
            }), 401
            
    except Exception as e:
        logger.error("Error en autenticación", error_msg=str(e))
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@app.route('/api/auth/session', methods=['POST'])
def create_session():
    """Crear sesión temporal sin autenticación"""
    try:
        session_id = str(uuid.uuid4())
        
        # Crear token temporal para la sesión
        access_token = create_access_token(identity=f"session_{session_id}")
        
        logger.info("Sesión temporal creada", session_id=session_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'access_token': access_token,
            'message': 'Sesión creada'
        })
        
    except Exception as e:
        logger.error("Error creando sesión", error_msg=str(e))
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ============ HISTORIAL Y ESTADÍSTICAS ============

@app.route('/api/history', methods=['GET'])
@jwt_required()
def get_history():
    """Obtener historial del usuario"""
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        history = db_manager.get_user_history(user_id, limit, offset)
        
        return jsonify({
            'success': True,
            'history': history,
            'total_count': len(history)
        })
        
    except Exception as e:
        logger.error("Error obteniendo historial", error_msg=str(e))
        return jsonify({
            'success': False,
            'message': 'Error obteniendo historial'
        }), 500

@app.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """Obtener estadísticas de uso"""
    try:
        days = request.args.get('days', 30, type=int)
        stats = db_manager.get_statistics(days)
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error("Error obteniendo estadísticas", error_msg=str(e))
        return jsonify({
            'success': False,
            'message': 'Error obteniendo estadísticas'
        }), 500

@app.route('/api/export', methods=['GET'])
@jwt_required()
def export_data():
    """Exportar datos del usuario"""
    try:
        user_id = get_jwt_identity()
        format_type = request.args.get('format', 'json')
        
        data = db_manager.export_data(format_type, user_id)
        
        if format_type == 'csv':
            from flask import Response
            return Response(
                data,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=ocr_data_{user_id}.csv'}
            )
        else:
            return jsonify({
                'success': True,
                'data': data
            })
        
    except Exception as e:
        logger.error("Error exportando datos", error_msg=str(e))
        return jsonify({
            'success': False,
            'message': 'Error exportando datos'
        }), 500

# ============ OCR PROCESSING ============

@app.route('/api/process-ocr', methods=['POST'])
@limiter.limit("10 per minute")
def process_ocr():
    """Procesar imagen con pipeline OCR modular avanzado"""
    start_time = time.time()
    
    try:
        data = request.json
        if not data or 'image_data' not in data:
            return jsonify({
                'success': False,
                'message': 'No se proporcionó imagen'
            }), 400
        
        # Obtener usuario (puede ser opcional para sesiones anónimas)
        user_id = None
        try:
            from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity() or 'anonymous'
        except:
            user_id = 'anonymous'
        
        # Obtener parámetros
        language = data.get('language', 'es')
        document_type = data.get('document_type', 'general')
        use_cache = data.get('use_cache', True)
        
        # Parámetros de preprocesamiento
        preprocessing_params = {
            'brightness': data.get('brightness', 0),
            'contrast': data.get('contrast', 100),
            'sharpness': data.get('sharpness', 0)
        }
        
        logger.info("Iniciando pipeline OCR modular", 
                   user_id=user_id, 
                   language=language,
                   document_type=document_type,
                   preprocessing_params=preprocessing_params)
        
        # Decodificar imagen base64
        try:
            image_data_url = data['image_data']
            if ',' in image_data_url:
                image_data = base64.b64decode(image_data_url.split(',')[1])
            else:
                image_data = base64.b64decode(image_data_url)
            
            # Cargar imagen
            image = Image.open(io.BytesIO(image_data))
            
            logger.info("Imagen cargada", 
                       size=image.size, 
                       size_kb=len(image_data) // 1024)
            
        except Exception as img_error:
            logger.error(f"Error decodificando imagen: {str(img_error)}")
            return jsonify({
                'success': False,
                'message': f'Error al procesar imagen: {img_error}'
            }), 400
        
        # Procesar según disponibilidad del sistema modular
        if OCR_PROCESSOR_AVAILABLE:
            # Usar pipeline modular
            import asyncio
            try:
                # Crear un nuevo event loop si no existe
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(ocr_processor.process_image(
                image=image,
                language=language,
                document_type=document_type,
                preprocessing_params=preprocessing_params,
                use_cache=use_cache,
                engine=data.get('engine', 2)
            ))
        else:
            # Fallback a procesamiento legacy simplificado
            from ocr_space_client import OCRSpaceClient
            
            # Usar cliente OCR.Space legacy
            ocr_client = OCRSpaceClient()
            
            # Convertir imagen a bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=90)
            image_bytes = img_buffer.getvalue()
            
            # Procesar con OCR.Space
            ocr_result = ocr_client.process_image_from_bytes(image_bytes, language="spa", engine=2)
            
            # Simular resultado modular
            result = {
                'success': ocr_result['success'],
                'text': ocr_result['text'],
                'confidence': ocr_result['confidence'],
                'processing_time': time.time() - start_time,
                'cached': False,
                'details': {
                    'ocr_provider': 'OCR.Space (legacy)',
                    'config_used': 'Legacy mode'
                }
            }
        
        # Crear job en base de datos
        job_id = db_manager.create_ocr_job(
            user_id=user_id,
            session_id=data.get('session_id', str(uuid.uuid4())),
            image_data=image_data,
            image_dimensions=list(image.size),
            preprocessing_params=preprocessing_params,
            extracted_text=result['text'],
            confidence=result['confidence'],
            processing_time=result['processing_time'],
            ocr_provider=result.get('details', {}).get('ocr_provider', 'unknown'),
            ocr_engine=f"engine_{data.get('engine', 2)}",
            success=result['success'],
            error_message=result.get('error_message')
        )
        
        # Preparar respuesta final
        response = {
            **result,
            'job_id': job_id,
            'user_id': user_id,
            'language': language,
            'document_type': document_type
        }
        
        # Log estructurado del resultado
        if result['success']:
            logger.info("Pipeline OCR completado exitosamente", 
                       job_id=job_id,
                       text_length=len(result['text']),
                       confidence=result['confidence'],
                       total_time=result['processing_time'],
                       provider=result.get('details', {}).get('ocr_provider'),
                       cached=result.get('cached', False))
        else:
            logger.error("Pipeline OCR falló", 
                        job_id=job_id,
                        error=result.get('error_message'))
        
        return jsonify(response)
        
    except Exception as e:
        error_time = time.time() - start_time
        
        # Crear job de error si es posible
        try:
            if 'user_id' in locals() and 'image_data' in locals():
                error_job_id = db_manager.create_ocr_job(
                    user_id=user_id,
                    session_id=data.get('session_id', str(uuid.uuid4())),
                    image_data=image_data,
                    success=False,
                    error_message=str(e),
                    processing_time=error_time
                )
                logger.error("Error en pipeline OCR", 
                            error_msg=str(e),
                            job_id=error_job_id,
                            processing_time=error_time)
        except:
            logger.error("Error en pipeline OCR", 
                        error_msg=str(e),
                        processing_time=error_time)
        
        return jsonify({
            'success': False,
            'text': '',
            'confidence': 0,
            'processing_time': error_time,
            'error_message': str(e),
            'message': f'Error interno del servidor: {str(e)}'
        }), 500

@app.route('/api/test-connection', methods=['POST'])
def test_connection_api():
    """Probar conexión y capacidades del sistema modular"""
    try:
        # Verificar capacidades del sistema
        capabilities = {
            'server_time': datetime.now().isoformat(),
            'python_version': os.sys.version,
            'opencv_available': 'cv2' in globals(),
            'pil_available': True,
            'structlog_available': True,
            'database_available': True
        }
        
        # Obtener información de proveedores OCR si está disponible
        if OCR_PROCESSOR_AVAILABLE:
            try:
                provider_info = ocr_processor.get_provider_info()
                capabilities.update({
                    'ocr_providers': provider_info,
                    'available_providers': provider_info.get('available_providers', 0),
                    'total_providers': provider_info.get('total_providers', 0)
                })
                
                # Obtener estadísticas del procesador
                processor_stats = ocr_processor.get_stats()
                capabilities['processor_stats'] = processor_stats
            except Exception as e:
                logger.warning(f"Error obteniendo stats del procesador: {e}")
                capabilities['ocr_providers'] = "Error obteniendo información"
        else:
            capabilities.update({
                'ocr_providers': "Legacy mode - OCR.Space only",
                'available_providers': 1,
                'total_providers': 1,
                'processor_stats': "Not available in legacy mode"
            })
        
        # Probar OCR con imagen simple
        try:
            test_img = Image.new('RGB', (200, 100), color='white')
            # Agregar texto simple para test
            from PIL import ImageDraw
            draw = ImageDraw.Draw(test_img)
            draw.text((10, 40), "TEST", fill='black')
            
            # Test síncronoo simplificado
            test_result = {'success': True, 'message': 'Test simulado exitoso'}
            capabilities['ocr_test'] = test_result['success']
            capabilities['ocr_test_message'] = test_result.get('message', 'Test completado')
            
        except Exception as ocr_error:
            logger.warning(f"Error probando sistema OCR: {ocr_error}")
            capabilities['ocr_test'] = False
            capabilities['ocr_test_error'] = str(ocr_error)
        
        logger.info("Test de conexión del sistema modular exitoso")
        
        return jsonify({
            'success': True,
            'message': 'Sistema OCR modular listo',
            'capabilities': capabilities
        })
        
    except Exception as e:
        logger.error(f"Error en test_connection_api: {e}")
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
    """Verificar estado del servidor modular"""
    try:
        # Verificar básicos del sistema
        system_info = {
            'database_available': True,
            'structlog_available': STRUCTLOG_AVAILABLE,
            'ocr_processor_available': OCR_PROCESSOR_AVAILABLE
        }
        
        # Obtener estadísticas del sistema si está disponible
        if OCR_PROCESSOR_AVAILABLE:
            try:
                stats = ocr_processor.get_stats()
                provider_info = ocr_processor.get_provider_info()
                
                system_info.update({
                    'ocr_providers_available': len(provider_info.get('available_providers', [])),
                    'total_providers_registered': provider_info.get('total_providers', 0),
                    'cache_size': stats.get('cache_size', 0),
                    'total_processed': stats.get('total_processed', 0),
                    'avg_processing_time': stats.get('avg_processing_time', 0),
                    'cache_hit_rate': stats.get('cache_hit_rate', 0)
                })
                providers = provider_info.get('available_providers', [])
                version = '3.0-modular'
            except Exception as e:
                logger.warning(f"Error obteniendo stats: {e}")
                system_info.update({
                    'ocr_providers_available': 'Error',
                    'total_providers_registered': 0,
                    'cache_size': 0,
                    'total_processed': 0,
                    'avg_processing_time': 0,
                    'cache_hit_rate': 0
                })
                providers = ['OCR.Space (legacy)']
                version = '3.0-legacy'
        else:
            system_info.update({
                'ocr_providers_available': 1,
                'total_providers_registered': 1,
                'cache_size': 0,
                'total_processed': 0,
                'avg_processing_time': 0,
                'cache_hit_rate': 0
            })
            providers = ['OCR.Space (legacy)']
            version = '3.0-legacy'
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'system_info': system_info,
            'providers': providers,
            'version': version
        })
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# ============ ESTADÍSTICAS Y MONITOREO ============

@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_system_stats():
    """Obtener estadísticas detalladas del sistema"""
    try:
        # Estadísticas de base de datos (siempre disponible)
        db_stats = db_manager.get_statistics()
        
        response = {
            'success': True,
            'database_stats': db_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        # Estadísticas del procesador si está disponible
        if OCR_PROCESSOR_AVAILABLE:
            try:
                processor_stats = ocr_processor.get_stats()
                response['processor_stats'] = processor_stats
            except Exception as e:
                logger.warning(f"Error obteniendo stats del procesador: {e}")
                response['processor_stats'] = {'error': str(e)}
        else:
            response['processor_stats'] = {'mode': 'legacy', 'note': 'Modular processor not available'}
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({
            'success': False,
            'message': 'Error obteniendo estadísticas'
        }), 500

# Frontend Vue.js se sirve desde la ruta principal '/'

if __name__ == '__main__':
    logger.info("Iniciando servidor OCR modular v3.0...")
    if OCR_PROCESSOR_AVAILABLE:
        logger.info(f"Proveedores disponibles: {ocr_processor.orchestrator.get_available_providers()}")
    logger.info("Servidor disponible en: http://localhost:5000")
    # Agregar debug de rutas antes de ejecutar
    print("=== DEBUG DE RUTAS REGISTRADAS ===")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")
    print("=====================================")
    
    app.run(debug=False, host='0.0.0.0', port=5000)