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
    
    # Simular carga de Tesseract
    send_test_log('DEBUG', 'Cargando Tesseract.js desde CDN principal')
    time.sleep(0.5)
    send_test_log('INFO', 'Tesseract.js cargado correctamente', {
        'version': '4.1.1',
        'languages': ['eng', 'spa', 'fra', 'deu']
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
    send_test_log('INFO', '=== INICIO PROCESAMIENTO OCR ===', {
        'tesseractAvailable': True,
        'canvasValid': True,
        'canvasSize': '1280x720',
        'workerActive': False,
        'debugMode': True
    })
    
    time.sleep(0.5)
    
    send_test_log('DEBUG', 'Creando worker de Tesseract...')
    time.sleep(0.3)
    send_test_log('DEBUG', 'Worker creado sin idioma, cargando idioma español...')
    time.sleep(0.3)
    send_test_log('INFO', 'Worker creado exitosamente con español')
    
    time.sleep(0.5)
    
    send_test_log('INFO', 'OCR completado exitosamente', {
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