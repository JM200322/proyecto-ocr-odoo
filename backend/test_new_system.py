#!/usr/bin/env python3
"""
Script de prueba para el nuevo sistema OCR modular
"""

import sys
import os
import time
import asyncio
from PIL import Image, ImageDraw, ImageFont

# Agregar paths para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db_manager
from src.core.ocr_processor import ocr_processor
from src.core.image_preprocessor import image_preprocessor
from src.core.text_postprocessor import text_postprocessor

def create_test_image_with_text(text: str, size: tuple = (400, 200)) -> Image.Image:
    """Crear imagen de prueba con texto"""
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        # Intentar usar una fuente del sistema
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        # Fallback a fuente por defecto
        font = ImageFont.load_default()
    
    # Centrar texto
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    
    draw.text((x, y), text, fill='black', font=font)
    return img

async def test_image_preprocessing():
    """Probar módulo de preprocesamiento de imagen"""
    print("\n🔧 === PRUEBA DE PREPROCESAMIENTO ===")
    
    # Crear imagen de prueba
    test_img = create_test_image_with_text("PREPROCESAMIENTO TEST")
    print(f"✅ Imagen de prueba creada: {test_img.size}")
    
    # Probar preprocesamiento básico
    params = {'brightness': 10, 'contrast': 120, 'sharpness': 15}
    processed_img = image_preprocessor.preprocess_advanced(test_img, **params)
    print(f"✅ Preprocesamiento básico: {processed_img.size}")
    
    # Probar optimización por tipo de documento
    invoice_img = image_preprocessor.optimize_for_ocr(test_img, 'invoice')
    print(f"✅ Optimización para factura: {invoice_img.size}")
    
    # Probar detección de límites
    bounds = image_preprocessor.detect_document_bounds(test_img)
    if bounds:
        print(f"✅ Límites detectados: {bounds}")
    else:
        print("⚠️ No se detectaron límites del documento")

def test_text_postprocessing():
    """Probar módulo de post-procesamiento de texto"""
    print("\n✨ === PRUEBA DE POST-PROCESAMIENTO ===")
    
    # Texto con errores típicos de OCR
    test_texts = [
        "Hola mund0, este es un test de 0CR",
        "FACTURA N° 12345\nTOTAL: 1OO,5O €",
        "em@il: test@example.com\nTeléfono: 123 456 789",
        "Dirección:  Calle   Principal  ,   123"
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\n--- Test {i+1} ---")
        print(f"Original: {repr(text)}")
        
        result = text_postprocessor.process_advanced(text, 'es', 'general')
        print(f"Procesado: {repr(result['text'])}")
        print(f"Confianza: {result['confidence_score']:.2f}")
        print(f"Correcciones: {result['corrections_applied']}")
        
        if result['detected_elements']:
            print(f"Elementos detectados: {result['detected_elements']}")

async def test_ocr_providers():
    """Probar proveedores OCR"""
    print("\n🔍 === PRUEBA DE PROVEEDORES OCR ===")
    
    # Obtener información de proveedores
    provider_info = ocr_processor.get_provider_info()
    print(f"✅ Proveedores disponibles: {provider_info['available_providers']}")
    print(f"✅ Total proveedores: {provider_info['total_providers']}")
    
    # Crear imagen de prueba con texto más legible
    test_img = create_test_image_with_text("PRUEBA OCR MODULAR", (500, 150))
    
    # Probar pipeline completo
    print("\n🚀 Probando pipeline completo...")
    start_time = time.time()
    
    result = await ocr_processor.process_image(
        image=test_img,
        language='es',
        document_type='general',
        preprocessing_params={'brightness': 0, 'contrast': 100, 'sharpness': 0}
    )
    
    processing_time = time.time() - start_time
    
    print(f"✅ Pipeline completado en {processing_time:.2f}s")
    print(f"Resultado exitoso: {result['success']}")
    print(f"Texto extraído: {repr(result['text'])}")
    print(f"Confianza: {result['confidence']:.2f}")
    print(f"Cached: {result.get('cached', False)}")
    
    if result.get('details'):
        details = result['details']
        print(f"Proveedor usado: {details.get('ocr_provider', 'N/A')}")
        print(f"Tiempo preprocesamiento: {details.get('preprocessing_time', 0):.2f}s")
        print(f"Tiempo OCR: {details.get('ocr_time', 0):.2f}s")
        print(f"Tiempo post-procesamiento: {details.get('postprocessing_time', 0):.2f}s")

def test_database():
    """Probar sistema de base de datos"""
    print("\n💾 === PRUEBA DE BASE DE DATOS ===")
    
    # Crear job de prueba
    test_image_data = b"fake_image_data_for_testing"
    
    job_id = db_manager.create_ocr_job(
        user_id="test_user",
        session_id="test_session",
        image_data=test_image_data,
        image_dimensions=[400, 200],
        preprocessing_params={'brightness': 10, 'contrast': 120},
        extracted_text="Texto de prueba extraído",
        confidence=85.5,
        processing_time=2.34,
        ocr_provider="OCR.Space",
        ocr_engine="engine_2",
        success=True
    )
    
    print(f"✅ Job creado con ID: {job_id}")
    
    # Obtener job
    job = db_manager.get_ocr_job(job_id)
    if job:
        print(f"✅ Job recuperado: ID={job['id']}, Usuario={job['user_id']}")
        print(f"   Texto: {job['extracted_text'][:50]}...")
        print(f"   Confianza: {job['confidence']}%")
    
    # Probar cache por hash
    image_hash = db_manager.calculate_image_hash(test_image_data)
    cached = db_manager.find_by_image_hash(image_hash)
    if cached:
        print(f"✅ Cache funciona: Hash={image_hash[:16]}...")
    
    # Obtener estadísticas
    stats = db_manager.get_statistics(days=1)
    print(f"✅ Estadísticas: {stats['total_jobs']} jobs, {stats['successful_jobs']} exitosos")
    
    # Limpiar datos de prueba
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ocr_jobs WHERE user_id = 'test_user'")
        print("✅ Datos de prueba limpiados")
    except Exception as e:
        print(f"⚠️ Error limpiando datos de prueba: {e}")

async def test_performance():
    """Probar rendimiento del sistema"""
    print("\n⚡ === PRUEBA DE RENDIMIENTO ===")
    
    test_images = [
        create_test_image_with_text("PERFORMANCE TEST 1"),
        create_test_image_with_text("RENDIMIENTO PRUEBA 2", (300, 150)),
        create_test_image_with_text("VELOCIDAD TEST 3", (600, 200))
    ]
    
    total_time = 0
    successful_processes = 0
    
    for i, img in enumerate(test_images):
        print(f"\n--- Procesando imagen {i+1} ---")
        start_time = time.time()
        
        result = await ocr_processor.process_image(
            image=img,
            language='es',
            document_type='general'
        )
        
        processing_time = time.time() - start_time
        total_time += processing_time
        
        if result['success']:
            successful_processes += 1
            print(f"✅ Exitoso en {processing_time:.2f}s: {repr(result['text'])}")
        else:
            print(f"❌ Falló en {processing_time:.2f}s: {result.get('error_message', 'Error desconocido')}")
    
    avg_time = total_time / len(test_images)
    success_rate = (successful_processes / len(test_images)) * 100
    
    print(f"\n📊 RESULTADOS DE RENDIMIENTO:")
    print(f"   Tiempo total: {total_time:.2f}s")
    print(f"   Tiempo promedio: {avg_time:.2f}s")
    print(f"   Tasa de éxito: {success_rate:.1f}%")
    print(f"   Procesos exitosos: {successful_processes}/{len(test_images)}")

async def main():
    """Función principal de pruebas"""
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA OCR MODULAR v3.0")
    print("=" * 60)
    
    try:
        # Pruebas de módulos individuales
        await test_image_preprocessing()
        test_text_postprocessing()
        test_database()
        
        # Pruebas de integración
        await test_ocr_providers()
        
        # Pruebas de rendimiento
        await test_performance()
        
        # Estadísticas finales
        print("\n📊 === ESTADÍSTICAS FINALES ===")
        stats = ocr_processor.get_stats()
        print(f"Cache size: {stats['cache_size']}")
        print(f"Total procesado: {stats['total_processed']}")
        print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
        print(f"Tiempo promedio: {stats['avg_processing_time']:.2f}s")
        
        provider_stats = ocr_processor.get_provider_info()
        print(f"Proveedores disponibles: {provider_stats['available_providers']}")
        
        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        
    except Exception as e:
        print(f"\n❌ ERROR EN PRUEBAS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())