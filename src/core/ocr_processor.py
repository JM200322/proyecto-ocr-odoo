#!/usr/bin/env python3
"""
Procesador principal de OCR que coordina preprocesamiento, OCR y post-procesamiento
"""

import time
import logging
from typing import Dict, Any, Optional, List
from PIL import Image
import hashlib

from .image_preprocessor import image_preprocessor
from .text_postprocessor import text_postprocessor
from ..integrations.ocr_providers.base_provider import ocr_orchestrator, OCRResult
from ..integrations.ocr_providers.ocr_space import create_ocr_space_provider
from ..integrations.ocr_providers.tesseract import create_tesseract_provider

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Procesador principal que coordina todo el pipeline de OCR"""
    
    def __init__(self):
        self.orchestrator = ocr_orchestrator
        self.cache = {}  # Cache simple en memoria
        self.stats = {
            'total_processed': 0,
            'cache_hits': 0,
            'provider_usage': {},
            'avg_processing_time': 0.0,
            'total_processing_time': 0.0
        }
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Inicializar y registrar proveedores OCR"""
        
        # Registrar OCR.Space como proveedor principal
        try:
            ocr_space = create_ocr_space_provider()
            self.orchestrator.register_provider(ocr_space)
            logger.info("OCR.Space registrado como proveedor principal")
        except Exception as e:
            logger.error(f"Error registrando OCR.Space: {e}")
        
        # Registrar Tesseract como fallback
        try:
            tesseract = create_tesseract_provider()
            self.orchestrator.register_provider(tesseract)
            logger.info("Tesseract registrado como proveedor fallback")
        except Exception as e:
            logger.warning(f"Tesseract no disponible como fallback: {e}")
        
        available_providers = self.orchestrator.get_available_providers()
        logger.info(f"Proveedores OCR disponibles: {available_providers}")
    
    async def process_image(
        self,
        image: Image.Image,
        language: str = 'es',
        document_type: str = 'general',
        preprocessing_params: Dict = None,
        use_cache: bool = True,
        digits_only: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Procesar imagen completa con pipeline optimizado
        
        Args:
            image: Imagen PIL a procesar
            language: Código de idioma (es, en, etc.)
            document_type: Tipo de documento (general, invoice, contact, etc.)
            preprocessing_params: Parámetros específicos de preprocesamiento
            use_cache: Usar cache si está disponible
            **kwargs: Parámetros adicionales para OCR
            
        Returns:
            Dict con resultado completo del procesamiento
        """
        
        start_time = time.time()
        pipeline_log = []
        
        try:
            # 1. Calcular hash de imagen para cache
            image_hash = self._calculate_image_hash(image)
            pipeline_log.append(f"📊 Hash calculado: {image_hash[:16]}")
            
            # 2. Verificar cache
            if use_cache and image_hash in self.cache:
                self.stats['cache_hits'] += 1
                cached_result = self.cache[image_hash].copy()
                cached_result['cached'] = True
                cached_result['processing_time'] = time.time() - start_time
                pipeline_log.append("🎯 Resultado obtenido del cache")
                
                logger.info("Cache hit para imagen", image_hash=image_hash[:16])
                return cached_result
            
            # 3. Preprocesamiento de imagen
            pipeline_log.append("🔧 Iniciando preprocesamiento...")
            preprocess_start = time.time()
            
            # Usar parámetros específicos o detectar automáticamente
            if preprocessing_params is None:
                preprocessing_params = self._detect_optimal_preprocessing(image, document_type)
            
            processed_image = image_preprocessor.optimize_for_ocr(image, document_type)
            if preprocessing_params:
                processed_image = image_preprocessor.preprocess_advanced(
                    processed_image, 
                    **preprocessing_params
                )
            
            preprocess_time = time.time() - preprocess_start
            pipeline_log.append(f"✅ Preprocesamiento completado en {preprocess_time:.2f}s")
            
            # 4. Detección de límites del documento (opcional)
            document_bounds = image_preprocessor.detect_document_bounds(processed_image)
            if document_bounds:
                pipeline_log.append(f"📄 Documento detectado en: {document_bounds}")
            
            # 5. Procesamiento OCR con múltiples proveedores
            pipeline_log.append("🔍 Iniciando OCR...")
            ocr_start = time.time()
            
            ocr_result = await self.orchestrator.process_with_fallback(
                processed_image,
                language=language,
                digits_only=digits_only,
                **kwargs
            )
            
            ocr_time = time.time() - ocr_start
            pipeline_log.append(f"✅ OCR completado con {ocr_result.provider} en {ocr_time:.2f}s")
            
            # 6. Post-procesamiento del texto
            pipeline_log.append("✨ Iniciando post-procesamiento...")
            postprocess_start = time.time()
            
            postprocess_result = text_postprocessor.process_advanced(
                ocr_result.text,
                language=language,
                document_type=document_type
            )
            
            postprocess_time = time.time() - postprocess_start
            pipeline_log.append(f"✅ Post-procesamiento completado en {postprocess_time:.2f}s")
            
            # 7. Combinar resultados y calcular métricas finales
            total_time = time.time() - start_time
            
            # Combinar confianza de OCR y post-procesamiento
            final_confidence = (
                ocr_result.confidence * 0.7 + 
                postprocess_result['confidence_score'] * 0.3
            )
            
            final_result = {
                'success': ocr_result.success and len(postprocess_result['text'].strip()) > 0,
                'text': postprocess_result['text'],
                'confidence': final_confidence,
                'processing_time': total_time,
                'cached': False,
                'image_hash': image_hash,
                'pipeline_log': pipeline_log,
                'details': {
                    'preprocessing_time': preprocess_time,
                    'preprocessing_params': preprocessing_params,
                    'ocr_time': ocr_time,
                    'ocr_provider': ocr_result.provider,
                    'ocr_confidence': ocr_result.confidence,
                    'postprocessing_time': postprocess_time,
                    'postprocessing_stats': postprocess_result,
                    'document_bounds': document_bounds,
                    'text_length': len(postprocess_result['text']),
                    'language_used': language,
                    'document_type': document_type
                }
            }
            
            # 8. Guardar en cache si fue exitoso
            if final_result['success'] and use_cache:
                self.cache[image_hash] = final_result.copy()
                pipeline_log.append("💾 Resultado guardado en cache")
                
                # Limpiar cache si es muy grande (simple LRU)
                if len(self.cache) > 100:
                    oldest_key = min(self.cache.keys())
                    del self.cache[oldest_key]
            
            # 9. Actualizar estadísticas
            self._update_stats(final_result)
            
            logger.info(f"Pipeline OCR completado: success={final_result['success']}, confidence={final_confidence:.1f}, provider={ocr_result.provider}, time={total_time:.2f}s")
            
            return final_result
            
        except Exception as e:
            error_time = time.time() - start_time
            pipeline_log.append(f"❌ Error en pipeline: {str(e)}")
            
            logger.error(f"Error en pipeline OCR: {str(e)}, processing_time={error_time}")
            
            return {
                'success': False,
                'text': '',
                'confidence': 0.0,
                'processing_time': error_time,
                'cached': False,
                'error_message': str(e),
                'pipeline_log': pipeline_log
            }
    
    def _calculate_image_hash(self, image: Image.Image) -> str:
        """Calcular hash único de la imagen para cache"""
        # Convertir imagen a bytes para hash
        import io
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        image_bytes = img_buffer.getvalue()
        
        return hashlib.sha256(image_bytes).hexdigest()
    
    def _detect_optimal_preprocessing(self, image: Image.Image, document_type: str) -> Dict:
        """Detectar parámetros óptimos de preprocesamiento automáticamente"""
        
        # Análisis básico de la imagen
        width, height = image.size
        aspect_ratio = width / height
        
        # Convertir a escala de grises para análisis
        gray_image = image.convert('L') if image.mode != 'L' else image
        
        # Calcular estadísticas de intensidad
        import numpy as np
        img_array = np.array(gray_image)
        mean_intensity = np.mean(img_array)
        std_intensity = np.std(img_array)
        
        params = {
            'brightness': 0,
            'contrast': 100,
            'sharpness': 0
        }
        
        # Ajustar basándose en análisis
        if mean_intensity < 100:  # Imagen oscura
            params['brightness'] = 15
            params['contrast'] = 120
        elif mean_intensity > 200:  # Imagen muy clara
            params['brightness'] = -10
            params['contrast'] = 110
        
        if std_intensity < 30:  # Bajo contraste
            params['contrast'] = 130
            params['sharpness'] = 15
        
        # Ajustes específicos por tipo de documento
        if document_type == 'invoice':
            params['contrast'] = max(params['contrast'], 125)
            params['sharpness'] = max(params['sharpness'], 10)
        elif document_type == 'handwriting':
            params['sharpness'] = 0  # No aplicar sharpening a escritura manual
            params['contrast'] = min(params['contrast'], 110)
        
        logger.debug(f"Parámetros automáticos detectados: {params}")
        return params
    
    def _update_stats(self, result: Dict):
        """Actualizar estadísticas de uso"""
        self.stats['total_processed'] += 1
        
        provider = result.get('details', {}).get('ocr_provider', 'unknown')
        if provider not in self.stats['provider_usage']:
            self.stats['provider_usage'][provider] = 0
        self.stats['provider_usage'][provider] += 1
        
        processing_time = result.get('processing_time', 0)
        self.stats['total_processing_time'] += processing_time
        self.stats['avg_processing_time'] = (
            self.stats['total_processing_time'] / self.stats['total_processed']
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de uso del procesador"""
        cache_size = len(self.cache)
        cache_hit_rate = (
            self.stats['cache_hits'] / max(self.stats['total_processed'], 1) * 100
        )
        
        return {
            **self.stats,
            'cache_size': cache_size,
            'cache_hit_rate': cache_hit_rate,
            'available_providers': self.orchestrator.get_available_providers(),
            'provider_stats': self.orchestrator.get_provider_stats()
        }
    
    def clear_cache(self):
        """Limpiar cache de resultados"""
        self.cache.clear()
        logger.info("Cache de OCR limpiado")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Obtener información de proveedores disponibles"""
        return self.orchestrator.get_provider_stats()

# Instancia global del procesador
ocr_processor = OCRProcessor()