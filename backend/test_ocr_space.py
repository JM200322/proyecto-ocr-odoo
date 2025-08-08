#!/usr/bin/env python3
"""
Script de prueba para el nuevo sistema OCR.Space
"""

import requests
import base64
from PIL import Image
import io
import sys
import os

# Agregar el directorio actual al path para importar el módulo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ocr_space_client import OCRSpaceClient

def test_ocr_space_direct():
    """Probar OCR.Space directamente"""
    print("🧪 Probando OCR.Space directamente...")
    
    client = OCRSpaceClient()
    
    # Crear una imagen de prueba simple
    img = Image.new('RGB', (200, 100), color='white')
    
    # Agregar texto simple (esto no será reconocible por OCR, pero sirve para probar la API)
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    try:
        # Intentar usar una fuente del sistema
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        # Fallback a fuente por defecto
        font = ImageFont.load_default()
    
    draw.text((10, 40), "Test OCR", fill='black', font=font)
    
    # Guardar imagen temporal
    temp_path = "test_image.jpg"
    img.save(temp_path, "JPEG", quality=90)
    
    try:
        result = client.process_image_from_path(temp_path, language="spa", engine=2)
        
        print(f"✅ OCR.Space funcionando!")
        print(f"Texto extraído: {result.get('text', 'N/A')}")
        print(f"Confianza: {result.get('confidence', 'N/A')}%")
        print(f"Tiempo de procesamiento: {result.get('processing_time', 'N/A')}s")
        print(f"Éxito: {result.get('success', False)}")
        
        if not result.get('success'):
            print(f"Error: {result.get('message', 'Error desconocido')}")
            
    except Exception as e:
        print(f"❌ Error probando OCR.Space directamente: {e}")
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_ocr_endpoint():
    """Probar el endpoint de OCR actualizado"""
    print("\n🧪 Probando endpoint de OCR actualizado...")
    
    # Crear una imagen de prueba simple
    img = Image.new('RGB', (200, 100), color='white')
    
    # Agregar texto simple
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((10, 40), "Test OCR", fill='black', font=font)
    
    # Convertir a base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=90)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    
    # Preparar datos para la petición
    data = {
        'image_data': f'data:image/jpeg;base64,{img_data}',
        'brightness': 0,
        'contrast': 100,
        'sharpness': 0
    }
    
    try:
        # Hacer petición al endpoint
        response = requests.post(
            'http://localhost:5000/api/process-ocr',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Endpoint OCR funcionando correctamente!")
                print(f"Texto extraído: {result.get('text', 'N/A')}")
                print(f"Confianza: {result.get('confidence', 'N/A')}%")
                print(f"Tiempo de procesamiento: {result.get('processing_time', 'N/A')}s")
                print(f"Configuración usada: {result.get('details', {}).get('config_used', 'N/A')}")
            else:
                print("❌ Error en endpoint OCR:")
                print(result.get('message', 'Error desconocido'))
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servidor. Asegúrate de que esté ejecutándose.")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_health_endpoint():
    """Probar el endpoint de health check"""
    print("\n🏥 Probando health check...")
    
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Health check exitoso!")
            print(f"Estado: {result.get('status', 'N/A')}")
            print(f"OCR.Space disponible: {result.get('ocr_space_available', 'N/A')}")
            print(f"API Key configurada: {result.get('ocr_api_key_configured', 'N/A')}")
        else:
            print(f"❌ Health check falló: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servidor.")
    except Exception as e:
        print(f"❌ Error en health check: {e}")

def main():
    print("🚀 Iniciando pruebas del nuevo sistema OCR.Space...")
    print("=" * 50)
    
    # Probar OCR.Space directamente
    test_ocr_space_direct()
    
    # Probar endpoints del servidor
    test_health_endpoint()
    test_ocr_endpoint()
    
    print("\n" + "=" * 50)
    print("✅ Pruebas completadas!")

if __name__ == "__main__":
    main() 