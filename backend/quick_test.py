#!/usr/bin/env python3
import requests
import json

def test_health():
    """Probar el endpoint de health check"""
    try:
        response = requests.get('http://localhost:5000/api/health')
        print("✅ Health check exitoso:")
        print(json.dumps(response.json(), indent=2))
        return True
    except Exception as e:
        print(f"❌ Error en health check: {e}")
        return False

def test_connection():
    """Probar el endpoint de test connection"""
    try:
        response = requests.post('http://localhost:5000/api/test-connection')
        print("✅ Test connection exitoso:")
        print(json.dumps(response.json(), indent=2))
        return True
    except Exception as e:
        print(f"❌ Error en test connection: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Probando endpoints del servidor...")
    
    if test_health():
        test_connection()
    else:
        print("❌ El servidor no está respondiendo") 