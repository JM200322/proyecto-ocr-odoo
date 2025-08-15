#!/usr/bin/env python3
"""
Script de inicio rápido para el frontend Vue.js del proyecto OCR
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def check_node_npm():
    """Verificar que Node.js y npm estén instalados"""
    print("🔍 Verificando Node.js y npm...")
    
    try:
        # Verificar Node.js
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            raise FileNotFoundError("Node.js no encontrado")
        node_version = result.stdout.strip()
        print(f"✅ Node.js {node_version} disponible")
        
        # Verificar npm
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            raise FileNotFoundError("npm no encontrado")
        npm_version = result.stdout.strip()
        print(f"✅ npm {npm_version} disponible")
        
        return True
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Por favor instala Node.js desde: https://nodejs.org/")
        return False
    except Exception as e:
        print(f"❌ Error verificando Node.js/npm: {e}")
        return False

def check_vue_project():
    """Verificar que el proyecto Vue.js esté configurado"""
    print("🔍 Verificando proyecto Vue.js...")
    
    vue_dir = Path("frontend-vue")
    package_json = vue_dir / "package.json"
    node_modules = vue_dir / "node_modules"
    
    if not vue_dir.exists():
        print("❌ Error: Directorio frontend-vue no encontrado")
        return False
    
    if not package_json.exists():
        print("❌ Error: package.json no encontrado en frontend-vue")
        return False
    
    if not node_modules.exists():
        print("⚠️  Dependencias no instaladas. Instalando...")
        try:
            subprocess.run(['npm', 'install'], cwd=vue_dir, check=True, shell=True)
            print("✅ Dependencias instaladas correctamente")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando dependencias: {e}")
            return False
    
    print("✅ Proyecto Vue.js configurado correctamente")
    return True

def start_vue_dev_server():
    """Iniciar el servidor de desarrollo Vue.js"""
    print("🚀 Iniciando servidor de desarrollo Vue.js...")
    print("=" * 60)
    
    vue_dir = Path("frontend-vue")
    
    print("🌐 Frontend Vue.js iniciándose en: http://localhost:3000")
    print("🔧 Backend API debería estar en: https://proyecto-ocr-odoo-1.onrender.com")
    print("\n💡 Tips:")
    print("   - Usa Ctrl+C para detener el servidor")
    print("   - El navegador se abrirá automáticamente")
    print("   - Hot-reload habilitado para desarrollo")
    print("   - Revisa la consola del navegador para logs")
    print("=" * 60)
    
    try:
        # Abrir navegador después de un breve delay
        def open_browser():
            time.sleep(3)
            webbrowser.open('http://localhost:3000')
        
        import threading
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Iniciar servidor de desarrollo
        subprocess.run(['npm', 'run', 'dev'], cwd=vue_dir, check=True, shell=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error iniciando servidor: {e}")
        return False
    except FileNotFoundError:
        print("❌ Error: npm no encontrado. Verifica la instalación de Node.js")
        return False
    
    return True

def show_project_info():
    """Mostrar información del proyecto"""
    print("📱 OCR → Odoo Tool v3.0 - Frontend Vue.js")
    print("🚀 Iniciador del servidor de desarrollo")
    print("=" * 60)
    
    print("\n🎯 Características del frontend Vue.js:")
    print("   • Vue.js 3 con Composition API")
    print("   • Vite como herramienta de desarrollo")
    print("   • Componentes modulares y reutilizables")
    print("   • Hot-reload para desarrollo rápido")
    print("   • Build optimizado para producción")
    print("   • Interfaz responsive y moderna")
    
    print("\n📁 Estructura del proyecto:")
    print("   • frontend-vue/src/components/ - Componentes Vue")
    print("   • frontend-vue/src/config.js - Configuración del backend")
    print("   • frontend-vue/dist/ - Build de producción")
    
    print("\n🔗 URLs importantes:")
    print("   • Frontend: http://localhost:3000")
    print("   • Backend: https://proyecto-ocr-odoo-1.onrender.com")
    print("   • Health Check: .../api/health")

def main():
    """Función principal"""
    show_project_info()
    
    # Verificaciones
    if not check_node_npm():
        sys.exit(1)
    
    if not check_vue_project():
        sys.exit(1)
    
    # Iniciar servidor
    if start_vue_dev_server():
        print("✅ Servidor Vue.js ejecutado correctamente")
    else:
        print("❌ Error ejecutando servidor Vue.js")
        sys.exit(1)

if __name__ == "__main__":
    main()