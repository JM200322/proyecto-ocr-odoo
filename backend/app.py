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
        uid = odoo_client.authenticate(instance)
        
        if uid:
            return jsonify({
                'success': True,
                'message': f'Conexión exitosa con instancia {instance}',
                'user_id': uid
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Error de conexión o credenciales incorrectas'
            }), 400
            
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

if __name__ == '__main__':
    # Verificar que existe la configuración
    if not os.path.exists('../config/credentials.json'):
        logger.warning("Archivo de credenciales no encontrado, se creará uno por defecto")
    
    app.run(debug=True, host='0.0.0.0', port=5000)