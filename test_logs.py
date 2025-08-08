#!/usr/bin/env python3
"""
Script de prueba para simular logs del frontend
"""
import requests
import json
import time
from datetime import datetime

def send_test_log(level, message, data=None):
    """Enviar log de prueba al backend"""
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/frontend-log',
            json={
                'level': level,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'data': data or {}
            }
        )
        
        if response.status_code == 200:
            print(f"✅ Log enviado: [{level}] {message}")
        else:
            print(f"❌ Error enviando log: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

def test_frontend_logs():
    """Probar diferentes tipos de logs del frontend"""
    print("🧪 Iniciando pruebas de logs del frontend...")
    print("=" * 50)
    
    # Simular inicio de aplicación
    send_test_log('INFO', 'Aplicación OCR iniciada', {
        'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'screenSize': '1920x1080',
        'backendUrl': 'http://127.0.0.1:5000'
    })
    
    time.sleep(1)
    
    # Simular verificación de backend
    send_test_log('DEBUG', 'Verificando conexión con backend OCR.Space')
    time.sleep(0.5)
    send_test_log('INFO', 'Backend OCR.Space conectado correctamente', {
        'apiKey': 'K86759595888957',
        'endpoint': 'https://api.ocr.space/parse/image',
        'engine': 2
    })
    
    time.sleep(1)
    
    # Simular inicio de cámara
    send_test_log('INFO', 'Iniciando cámara...', {
        'videoSize': '1280x720',
        'fps': 30,
        'streamActive': True
    })
    
    time.sleep(1)
    
    # Simular captura de foto
    send_test_log('INFO', 'Iniciando captura de foto', {
        'videoReady': True,
        'videoSize': '1280x720',
        'streamActive': True
    })
    
    time.sleep(0.5)
    
    send_test_log('INFO', 'Captura de foto completada', {
        'canvasSize': '1280x720',
        'dataUrlLength': 45678
    })
    
    time.sleep(1)
    
    # Simular procesamiento OCR
    send_test_log('INFO', '=== INICIO PROCESAMIENTO OCR.Space ===', {
        'backendAvailable': True,
        'canvasValid': True,
        'canvasSize': '1280x720',
        'apiKeyConfigured': True,
        'debugMode': True
    })
    
    time.sleep(0.5)
    
    send_test_log('DEBUG', 'Enviando imagen al servidor OCR.Space...')
    time.sleep(0.3)
    send_test_log('DEBUG', 'Imagen procesada, recibiendo respuesta...')
    time.sleep(0.3)
    send_test_log('INFO', 'OCR.Space completado exitosamente', {
        'textLength': 156,
        'confidence': 87.5,
        'textPreview': 'Este es un documento de prueba que contiene texto para ser procesado por el sistema OCR...'
    })
    
    time.sleep(1)
    
    # Simular envío a Odoo
    send_test_log('INFO', 'Enviando datos a Odoo...', {
        'textLength': 156,
        'documentType': 'contacts',
        'instance': 'production'
    })
    
    time.sleep(0.5)
    
    send_test_log('INFO', 'Datos enviados exitosamente a Odoo', {
        'recordId': 12345,
        'model': 'res.partner',
        'instance': 'production'
    })
    
    time.sleep(1)
    
    # Simular error
    send_test_log('ERROR', 'Error en procesamiento OCR', {
        'errorName': 'TypeError',
        'errorMessage': 'Cannot read properties of null (reading \'SetImageFile\')',
        'errorStack': 'Error: Cannot read properties of null (reading \'SetImageFile\')\n    at createWorker.js:191:1\n    at processOCR (index.html:966:1)',
        'errorString': 'TypeError: Cannot read properties of null (reading \'SetImageFile\')'
    })
    
    print("=" * 50)
    print("✅ Pruebas de logs completadas")
    print("📝 Revisa la consola del backend para ver los logs")

if __name__ == '__main__':
    test_frontend_logs() 