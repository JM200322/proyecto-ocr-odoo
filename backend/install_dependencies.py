#!/usr/bin/env python3
"""
Script para instalar dependencias del proyecto OCR
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

def install_tesseract():
    """Instalar Tesseract OCR"""
    system = platform.system().lower()
    
    print(f"Detectado sistema: {system}")
    
    if system == "windows":
        print("⚠️  Para Windows, necesitas instalar Tesseract manualmente:")
        print("1. Descarga desde: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Instala en C:\\Program Files\\Tesseract-OCR")
        print("3. Añade C:\\Program Files\\Tesseract-OCR al PATH")
        return True
        
    elif system == "darwin":  # macOS
        try:
            print("Instalando Tesseract con Homebrew...")
            subprocess.check_call(["brew", "install", "tesseract"])
            print("✅ Tesseract instalado correctamente")
            return True
        except subprocess.CalledProcessError:
            print("❌ Error instalando Tesseract. Asegúrate de tener Homebrew instalado.")
            return False
            
    elif system == "linux":
        try:
            print("Instalando Tesseract...")
            subprocess.check_call(["sudo", "apt-get", "update"])
            subprocess.check_call(["sudo", "apt-get", "install", "-y", "tesseract-ocr", "tesseract-ocr-spa"])
            print("✅ Tesseract instalado correctamente")
            return True
        except subprocess.CalledProcessError:
            print("❌ Error instalando Tesseract. Intenta manualmente:")
            print("sudo apt-get install tesseract-ocr tesseract-ocr-spa")
            return False
    
    else:
        print(f"⚠️  Sistema no reconocido: {system}")
        print("Instala Tesseract manualmente desde: https://github.com/tesseract-ocr/tesseract")
        return True

def verify_installation():
    """Verificar que todo esté instalado correctamente"""
    print("\nVerificando instalación...")
    
    # Verificar Tesseract
    try:
        result = subprocess.run(["tesseract", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Tesseract está instalado y funcionando")
        else:
            print("❌ Tesseract no está funcionando correctamente")
            return False
    except FileNotFoundError:
        print("❌ Tesseract no está instalado o no está en el PATH")
        return False
    
    # Verificar Python dependencies
    try:
        import PIL
        import pytesseract
        print("✅ Dependencias de Python instaladas correctamente")
    except ImportError as e:
        print(f"❌ Error importando dependencias: {e}")
        return False
    
    print("\n🎉 ¡Instalación completada exitosamente!")
    print("Puedes ejecutar el servidor con: python app.py")
    return True

def main():
    print("🚀 Instalador de dependencias para OCR")
    print("=" * 50)
    
    # Cambiar al directorio del script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Instalar dependencias
    if not install_python_dependencies():
        sys.exit(1)
    
    if not install_tesseract():
        sys.exit(1)
    
    # Verificar instalación
    if not verify_installation():
        print("\n❌ La instalación no se completó correctamente.")
        print("Revisa los errores anteriores e intenta de nuevo.")
        sys.exit(1)

if __name__ == "__main__":
    main() 