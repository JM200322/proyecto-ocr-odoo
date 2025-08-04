#!/usr/bin/env python3
"""
Script de prueba para el endpoint de OCR
"""

import requests
import base64
from PIL import Image
import io

def test_ocr_endpoint():
    """Probar el endpoint de OCR"""
    
    # Crear una imagen de prueba simple
    img = Image.new('RGB', (100, 50), color='white')
    
    # Convertir a base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_data = base64.b64encode(buffer.getvalue()).decode()
    
    # Preparar datos para la petición
    data = {
        'image_data': f'data:image/png;base64,{img_data}',
        'brightness': 0,
        'contrast': 100,
        'sharpness': 0
    }
    
    try:
        # Hacer petición al endpoint
        response = requests.post(
            'http://localhost:5000/api/process-ocr',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ OCR funcionando correctamente!")
                print(f"Texto extraído: {result.get('text', 'N/A')}")
                print(f"Confianza: {result.get('confidence', 'N/A')}%")
                print(f"Tiempo de procesamiento: {result.get('processing_time', 'N/A')}s")
            else:
                print("❌ Error en OCR:")
                print(result.get('message', 'Error desconocido'))
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servidor. Asegúrate de que esté ejecutándose.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Probando endpoint de OCR...")
    test_ocr_endpoint() 