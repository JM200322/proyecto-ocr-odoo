#!/usr/bin/env python3
"""
Script de inicio rápido para el servidor OCR con OCR.Space
"""

import os
import sys
import subprocess
import time

def check_dependencies():
    """Verificar que las dependencias estén instaladas"""
    print("🔍 Verificando dependencias...")
    
    try:
        import flask
        import requests
        from PIL import Image
        print("✅ Dependencias básicas disponibles")
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("Ejecuta: cd backend && python install_dependencies.py")
        return False
    
    try:
        from ocr_space_client import OCRSpaceClient
        print("✅ Cliente OCR.Space disponible")
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("Asegúrate de estar en el directorio backend")
        return False
    
    return True

def check_api_key():
    """Verificar que la API key esté configurada"""
    print("🔑 Verificando API key de OCR.Space...")
    
    try:
        from ocr_space_client import OCRSpaceClient
        client = OCRSpaceClient()
        
        if client.api_key and client.api_key != "K86759595888957":
            print("✅ API key configurada")
            return True
        else:
            print("⚠️  API key no configurada o usando valor por defecto")
            print("Ejecuta: cd backend && python setup_ocr_space.py")
            return False
    except Exception as e:
        print(f"❌ Error verificando API key: {e}")
        return False

def start_server():
    """Iniciar el servidor"""
    print("🚀 Iniciando servidor OCR con OCR.Space...")
    print("=" * 50)
    
    # Cambiar al directorio backend
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    if not os.path.exists(backend_dir):
        print("❌ Error: No se encontró el directorio backend")
        return False
    
    os.chdir(backend_dir)
    
    # Verificar dependencias
    if not check_dependencies():
        return False
    
    # Verificar API key
    if not check_api_key():
        print("\n💡 Puedes continuar con la API key por defecto, pero es recomendable configurar la tuya.")
        response = input("¿Continuar de todas formas? (s/n): ").lower()
        if response not in ['s', 'si', 'sí', 'y', 'yes']:
            return False
    
    print("\n🌐 Servidor iniciándose...")
    print("📱 Frontend disponible en: http://localhost:5000")
    print("🔧 API disponible en: http://localhost:5000/api/")
    print("\n💡 Tips:")
    print("   - Usa Ctrl+C para detener el servidor")
    print("   - Abre http://localhost:5000 en tu navegador")
    print("   - Verifica la conexión en: http://localhost:5000/api/health")
    print("=" * 50)
    
    try:
        # Iniciar el servidor Flask
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error iniciando servidor: {e}")
        return False
    except FileNotFoundError:
        print("❌ Error: No se encontró app.py en el directorio backend")
        return False
    
    return True

def main():
    """Función principal"""
    print("📱 OCR → Odoo Tool v3.0")
    print("🚀 Iniciador rápido del servidor")
    print("=" * 50)
    
    if start_server():
        print("✅ Servidor iniciado correctamente")
    else:
        print("❌ Error iniciando servidor")
        sys.exit(1)

if __name__ == "__main__":
    main() 