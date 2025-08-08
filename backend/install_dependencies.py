#!/usr/bin/env python3
"""
Script para instalar dependencias del proyecto OCR con OCR.Space
"""

import subprocess
import sys
import os
import platform

def install_python_dependencies():
    """Instalar dependencias de Python"""
    print("Instalando dependencias de Python...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencias de Python instaladas correctamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias de Python: {e}")
        return False
    return True

def setup_ocr_space():
    """Configurar OCR.Space API"""
    print("\n🔑 Configuración de OCR.Space API")
    print("=" * 40)
    print("Para usar el sistema OCR necesitas una API key gratuita:")
    print("1. Ve a https://ocr.space/ocrapi")
    print("2. Regístrate para obtener una API key gratuita")
    print("3. Ejecuta: python setup_ocr_space.py")
    print()
    
    setup_choice = input("¿Quieres configurar OCR.Space ahora? (s/n): ").lower().strip()
    if setup_choice in ['s', 'si', 'sí', 'y', 'yes']:
        try:
            subprocess.check_call([sys.executable, "setup_ocr_space.py"])
            print("✅ OCR.Space configurado correctamente")
            return True
        except subprocess.CalledProcessError:
            print("❌ Error configurando OCR.Space")
            return False
    else:
        print("⚠️  Recuerda configurar OCR.Space antes de usar el sistema")
        return True

def verify_installation():
    """Verificar que todo esté instalado correctamente"""
    print("\nVerificando instalación...")
    
    # Verificar Python dependencies
    try:
        import PIL
        import requests
        print("✅ Dependencias de Python instaladas correctamente")
    except ImportError as e:
        print(f"❌ Error importando dependencias: {e}")
        return False
    
    # Verificar OCR.Space
    try:
        from ocr_space_client import OCRSpaceClient
        client = OCRSpaceClient()
        print("✅ OCR.Space client disponible")
    except ImportError as e:
        print(f"❌ Error importando OCR.Space client: {e}")
        return False
    
    print("\n🎉 ¡Instalación completada exitosamente!")
    print("Puedes ejecutar el servidor con: python app.py")
    return True

def main():
    print("🚀 Instalador de dependencias para OCR con OCR.Space")
    print("=" * 50)
    
    # Cambiar al directorio del script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Instalar dependencias
    if not install_python_dependencies():
        sys.exit(1)
    
    # Configurar OCR.Space
    if not setup_ocr_space():
        sys.exit(1)
    
    # Verificar instalación
    if not verify_installation():
        print("\n❌ La instalación no se completó correctamente.")
        print("Revisa los errores anteriores e intenta de nuevo.")
        sys.exit(1)

if __name__ == "__main__":
    main() 