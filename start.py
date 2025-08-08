#!/usr/bin/env python3
"""
Script de conveniencia para iniciar el servidor OCR
"""

import os
import sys
import subprocess

def main():
    """Función principal"""
    print("📱 OCR → Odoo Tool v3.0")
    print("🚀 Iniciador de conveniencia")
    print("=" * 50)
    
    # Verificar que estamos en el directorio raíz
    if not os.path.exists('backend'):
        print("❌ Error: No se encontró el directorio backend")
        print("Asegúrate de ejecutar este script desde el directorio raíz del proyecto")
        sys.exit(1)
    
    # Cambiar al directorio backend
    os.chdir('backend')
    
    print("🔄 Cambiando al directorio backend...")
    print("🚀 Iniciando servidor...")
    print("=" * 50)
    
    try:
        # Ejecutar el script de inicio del backend
        subprocess.run([sys.executable, "start_server.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error iniciando servidor: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: No se encontró start_server.py en el directorio backend")
        sys.exit(1)

if __name__ == "__main__":
    main() 