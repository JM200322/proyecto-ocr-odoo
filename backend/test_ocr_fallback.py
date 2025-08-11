#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de fallback de motores OCR
"""

import time
import logging
from ocr_space_client import OCRSpaceClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ocr_fallback():
    """Probar el sistema de fallback de motores OCR"""
    client = OCRSpaceClient()
    
    print("🧪 Probando sistema de fallback de motores OCR...")
    print("=" * 60)
    
    # Crear una imagen de prueba simple
    from PIL import Image, ImageDraw, ImageFont
    
    # Crear imagen con texto de prueba
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        # Intentar usar una fuente del sistema
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        # Fallback a fuente por defecto
        font = ImageFont.load_default()
    
    # Dibujar texto de prueba
    text = "TEST OCR 123"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (400 - text_width) // 2
    y = (200 - text_height) // 2
    
    draw.text((x, y), text, fill='black', font=font)
    
    # Guardar imagen temporal
    test_image_path = "test_ocr_image.jpg"
    img.save(test_image_path, "JPEG", quality=90)
    
    print(f"📸 Imagen de prueba creada: {test_image_path}")
    print(f"📏 Dimensiones: {img.size}")
    print(f"📝 Texto incluido: '{text}'")
    print()
    
    # Probar con motor 2
    print("🔄 Probando con motor OCR 2...")
    try:
        result = client.process_image_from_path(test_image_path, language="spa", engine=2)
        
        if result["success"]:
            print(f"✅ Motor 2 exitoso:")
            print(f"   📝 Texto: '{result['text']}'")
            print(f"   🎯 Confianza: {result['confidence']:.1f}%")
            print(f"   ⏱️ Tiempo: {result['processing_time']:.2f}s")
        else:
            print(f"❌ Motor 2 falló: {result['message']}")
            
            # Probar con motor 3 como fallback
            print("\n🔄 Probando con motor OCR 3 como fallback...")
            try:
                result_fallback = client.process_image_from_path(test_image_path, language="spa", engine=3)
                
                if result_fallback["success"]:
                    print(f"✅ Motor 3 exitoso:")
                    print(f"   📝 Texto: '{result_fallback['text']}'")
                    print(f"   🎯 Confianza: {result_fallback['confidence']:.1f}%")
                    print(f"   ⏱️ Tiempo: {result_fallback['processing_time']:.2f}s")
                else:
                    print(f"❌ Motor 3 también falló: {result_fallback['message']}")
                    
            except Exception as e:
                print(f"❌ Error con motor 3: {e}")
                
    except Exception as e:
        print(f"❌ Error general: {e}")
    
    print("\n" + "=" * 60)
    
    # Limpiar archivo temporal
    import os
    if os.path.exists(test_image_path):
        os.remove(test_image_path)
        print(f"🧹 Archivo temporal eliminado: {test_image_path}")
    
    print("✅ Prueba completada")

def test_error_handling():
    """Probar el manejo de errores"""
    print("\n🔍 Probando manejo de errores...")
    print("=" * 60)
    
    client = OCRSpaceClient()
    
    # Probar con imagen muy pequeña (puede causar errores)
    img = Image.new('RGB', (10, 10), color='white')
    test_small_path = "test_small.jpg"
    img.save(test_small_path, "JPEG", quality=90)
    
    print("📸 Probando con imagen muy pequeña...")
    try:
        result = client.process_image_from_path(test_small_path, language="spa", engine=2)
        print(f"Resultado: {result}")
    except Exception as e:
        print(f"Error capturado: {e}")
    
    # Limpiar
    if os.path.exists(test_small_path):
        os.remove(test_small_path)
    
    print("✅ Prueba de manejo de errores completada")

if __name__ == "__main__":
    try:
        test_ocr_fallback()
        test_error_handling()
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        logging.exception("Error completo:") 