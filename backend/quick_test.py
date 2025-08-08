#!/usr/bin/env python3
"""
Script de prueba rápida para el nuevo sistema OCR.Space
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Probar que todas las dependencias están disponibles"""
    print("🔍 Probando imports...")
    
    try:
        from ocr_space_client import OCRSpaceClient
        print("✅ OCRSpaceClient importado correctamente")
    except ImportError as e:
        print(f"❌ Error importando OCRSpaceClient: {e}")
        return False
    
    try:
        import requests
        print("✅ requests disponible")
    except ImportError as e:
        print(f"❌ Error importando requests: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ PIL/Pillow disponible")
    except ImportError as e:
        print(f"❌ Error importando PIL: {e}")
        return False
    
    return True

def test_ocr_client():
    """Probar el cliente OCR"""
    print("\n🧪 Probando cliente OCR...")
    
    try:
        from ocr_space_client import OCRSpaceClient
        
        client = OCRSpaceClient()
        print(f"✅ Cliente OCR creado con API key: {client.api_key[:8]}...")
        
        # Crear imagen de prueba
        from PIL import Image
        img = Image.new('RGB', (100, 50), color='white')
        
        # Guardar temporalmente
        temp_path = "quick_test.jpg"
        img.save(temp_path, "JPEG", quality=90)
        
        # Probar procesamiento
        result = client.process_image_from_path(temp_path, language="spa", engine=2)
        
        # Limpiar
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if result.get('success'):
            print("✅ OCR funcionando correctamente!")
            print(f"   Texto extraído: {result.get('text', 'N/A')}")
            print(f"   Confianza: {result.get('confidence', 'N/A')}%")
            print(f"   Tiempo: {result.get('processing_time', 'N/A')}s")
        else:
            print(f"❌ OCR falló: {result.get('message', 'Error desconocido')}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error probando cliente OCR: {e}")
        return False

def test_app_import():
    """Probar que la app puede importar el nuevo sistema"""
    print("\n🔧 Probando import de app...")
    
    try:
        # Simular import de la app
        import importlib.util
        
        spec = importlib.util.spec_from_file_location("app", "app.py")
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        
        print("✅ App puede importar el nuevo sistema OCR")
        return True
        
    except Exception as e:
        print(f"❌ Error importando app: {e}")
        return False

def main():
    print("🚀 Prueba rápida del nuevo sistema OCR.Space")
    print("=" * 50)
    
    # Probar imports
    if not test_imports():
        print("\n❌ Faltan dependencias. Ejecuta: pip install -r requirements.txt")
        return False
    
    # Probar cliente OCR
    if not test_ocr_client():
        print("\n❌ Error en cliente OCR. Verifica tu API key.")
        return False
    
    # Probar app
    if not test_app_import():
        print("\n❌ Error en app. Revisa el código.")
        return False
    
    print("\n" + "=" * 50)
    print("✅ ¡Todo funcionando correctamente!")
    print("🎉 El nuevo sistema OCR.Space está listo para usar.")
    print("\nPara ejecutar el servidor:")
    print("  python app.py")
    print("\nPara probar el sistema completo:")
    print("  python test_ocr_space.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 