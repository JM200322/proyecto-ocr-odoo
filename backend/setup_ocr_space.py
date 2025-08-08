#!/usr/bin/env python3
"""
Script para configurar OCR.Space API
"""

import os
import sys
import re

def get_api_key():
    """Obtener API key del usuario"""
    print("🔑 Configuración de OCR.Space API")
    print("=" * 40)
    print("Para obtener una API key gratuita:")
    print("1. Ve a https://ocr.space/ocrapi")
    print("2. Regístrate para obtener una API key gratuita")
    print("3. Copia tu API key")
    print()
    
    while True:
        api_key = input("Ingresa tu API key de OCR.Space: ").strip()
        
        if not api_key:
            print("❌ La API key no puede estar vacía")
            continue
            
        # Validar formato básico de API key
        if len(api_key) < 10:
            print("❌ La API key parece ser muy corta")
            continue
            
        if not re.match(r'^[A-Za-z0-9]+$', api_key):
            print("❌ La API key contiene caracteres inválidos")
            continue
            
        return api_key

def update_ocr_client(api_key):
    """Actualizar el archivo ocr_space_client.py con la nueva API key"""
    client_file = "ocr_space_client.py"
    
    try:
        # Leer el archivo actual
        with open(client_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reemplazar la API key
        pattern = r'API_KEY = "[^"]*"'
        replacement = f'API_KEY = "{api_key}"'
        
        if re.search(pattern, content):
            new_content = re.sub(pattern, replacement, content)
        else:
            print("❌ No se encontró la línea API_KEY en el archivo")
            return False
        
        # Escribir el archivo actualizado
        with open(client_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ API key actualizada en {client_file}")
        return True
        
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo {client_file}")
        return False
    except Exception as e:
        print(f"❌ Error actualizando archivo: {e}")
        return False

def test_api_key(api_key):
    """Probar la API key"""
    print("\n🧪 Probando API key...")
    
    try:
        from ocr_space_client import OCRSpaceClient
        
        # Crear cliente con la nueva API key
        client = OCRSpaceClient(api_key)
        
        # Crear imagen de prueba simple
        from PIL import Image
        img = Image.new('RGB', (100, 50), color='white')
        
        # Guardar temporalmente
        temp_path = "test_setup.jpg"
        img.save(temp_path, "JPEG", quality=90)
        
        # Probar
        result = client.process_image_from_path(temp_path, language="spa", engine=2)
        
        # Limpiar
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if result.get('success'):
            print("✅ API key válida y funcionando!")
            return True
        else:
            print(f"❌ Error con API key: {result.get('message', 'Error desconocido')}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando API key: {e}")
        return False

def main():
    print("🚀 Configurando OCR.Space para el proyecto OCR → Odoo")
    print()
    
    # Obtener API key
    api_key = get_api_key()
    
    # Actualizar archivo
    if update_ocr_client(api_key):
        print("\n✅ Configuración completada!")
        print(f"API key configurada: {api_key[:8]}...")
        
        # Preguntar si quiere probar
        test = input("\n¿Quieres probar la API key ahora? (s/n): ").lower().strip()
        if test in ['s', 'si', 'sí', 'y', 'yes']:
            test_api_key(api_key)
    else:
        print("\n❌ Error en la configuración")
        sys.exit(1)
    
    print("\n🎉 ¡Configuración completada!")
    print("Ahora puedes ejecutar el servidor con: python app.py")

if __name__ == "__main__":
    main() 