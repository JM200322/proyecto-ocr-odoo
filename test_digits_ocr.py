#!/usr/bin/env python3
"""
Test para reconocimiento de dígitos en medidores
"""

import base64
import json
import requests
from PIL import Image, ImageDraw, ImageFont

def create_meter_test_image():
    """Crear imagen de prueba simulando un medidor digital"""
    # Crear imagen con fondo oscuro como medidor típico
    img = Image.new('RGB', (400, 120), 'black')
    draw = ImageDraw.Draw(img)
    
    # Simular display de medidor con números verdes
    try:
        # Intentar usar fuente monospace
        font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 48)
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 48)
        except:
            font = ImageFont.load_default()
    
    # Crear fondo de display (rectángulo gris oscuro)
    draw.rectangle([20, 20, 380, 100], fill='#1a1a1a', outline='#333333', width=2)
    
    # Números del medidor (simulando lectura 12345.67)
    number_text = "12345.67"
    
    # Dibujar números con color verde típico de displays
    draw.text((40, 35), number_text, fill='#00ff00', font=font)
    
    # Agregar algunas marcas/etiquetas que deberían ser ignoradas
    try:
        small_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 12)
    except:
        small_font = ImageFont.load_default()
    
    draw.text((300, 105), "kWh", fill='#888888', font=small_font)
    
    img.save('test_meter.jpg')
    print("Imagen de medidor creada: test_meter.jpg")
    return img

def test_digits_ocr(use_digits_mode=True):
    """Test OCR con modo dígitos"""
    
    # Crear imagen de prueba
    img = create_meter_test_image()
    
    # Convertir a base64
    with open('test_meter.jpg', 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Preparar request
    data = {
        'image_data': f'data:image/jpeg;base64,{image_data}',
        'language': 'es',
        'brightness': 0,
        'contrast': 100,
        'sharpness': 0,
        'digits_only': use_digits_mode
    }
    
    try:
        mode_text = "CON modo digitos" if use_digits_mode else "SIN modo digitos"
        print(f"\\nTesting OCR {mode_text}")
        print(f"Enviando a: http://127.0.0.1:5000/api/process-ocr")
        
        response = requests.post(
            'http://127.0.0.1:5000/api/process-ocr',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"EXITO!")
                print(f"Texto detectado: '{result.get('text', '')}'")
                print(f"Confianza: {result.get('confidence', 0)}%")
                print(f"Tiempo: {result.get('processing_time', 0):.2f}s")
                
                # Mostrar detalles si están disponibles
                details = result.get('details', {})
                if details:
                    print(f"Proveedor: {details.get('ocr_provider', 'N/A')}")
                    if details.get('preprocessing_time'):
                        print(f"Preprocesamiento: {details['preprocessing_time']:.2f}s")
                    if details.get('postprocessing_time'):
                        print(f"Post-procesamiento: {details['postprocessing_time']:.2f}s")
                
                return result.get('text', '')
            else:
                print(f"OCR fallo: {result.get('message', 'Error desconocido')}")
                return None
        else:
            print(f"Error HTTP {response.status_code}: {response.text[:200]}")
            return None
    
    except Exception as e:
        print(f"Error en request: {e}")
        return None

def compare_modes():
    """Comparar OCR normal vs modo dígitos"""
    print("="*60)
    print("COMPARACION: OCR Normal vs Modo Digitos")
    print("="*60)
    print("Imagen esperada: '12345.67' (medidor digital)")
    
    # Test sin modo dígitos
    result_normal = test_digits_ocr(use_digits_mode=False)
    
    # Test con modo dígitos
    result_digits = test_digits_ocr(use_digits_mode=True)
    
    print("\\n" + "="*60)
    print("RESUMEN:")
    print(f"OCR Normal:     '{result_normal or 'ERROR'}'")
    print(f"Modo Digitos:   '{result_digits or 'ERROR'}'")
    print(f"Valor esperado: '12345.67'")
    
    # Evaluar precisión
    expected = "12345.67"
    normal_correct = result_normal == expected if result_normal else False
    digits_correct = result_digits == expected if result_digits else False
    
    print("\\nEVALUACION:")
    print(f"OCR Normal {'CORRECTO' if normal_correct else 'INCORRECTO'}")
    print(f"Modo Digitos {'CORRECTO' if digits_correct else 'INCORRECTO'}")
    
    if digits_correct and not normal_correct:
        print("GANADOR: Modo Digitos es mas preciso!")
    elif normal_correct and not digits_correct:
        print("GANADOR: OCR Normal es mas preciso!")
    elif digits_correct and normal_correct:
        print("EMPATE: Ambos modos funcionan correctamente!")
    else:
        print("Ambos modos fallaron - revisar configuracion")

if __name__ == "__main__":
    compare_modes()