#!/usr/bin/env python3
"""
Test directo del OCR para verificar que funciona
"""

import requests
import base64
import json

# Crear una imagen de prueba simple
from PIL import Image, ImageDraw, ImageFont
import io

def create_test_image():
    """Crear una imagen simple con texto para probar"""
    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    # Intentar usar una fuente, si no está disponible usar la por defecto
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((20, 30), "Hello OCR Test 123", fill='black', font=font)
    
    # Convertir a base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/jpeg;base64,{image_data}"

def test_ocr():
    """Probar el OCR directamente"""
    print("🧪 Creando imagen de prueba...")
    image_data = create_test_image()
    
    print("📡 Enviando al servidor OCR...")
    
    payload = {
        "image_data": image_data,
        "brightness": 0,
        "contrast": 100,
        "sharpness": 0
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:5000/api/process-ocr",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Respuesta exitosa:")
            print(f"   🎯 Texto extraído: '{result.get('text', 'N/A')}'")
            print(f"   📈 Confianza: {result.get('confidence', 'N/A')}%")
            print(f"   ⏱️  Tiempo: {result.get('processing_time', 'N/A')}s")
            print(f"   🔧 Provider: {result.get('provider', 'N/A')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   📄 Respuesta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_ocr()