#!/usr/bin/env python3
"""
Interfaz base para proveedores de OCR
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class OCRProvider(ABC):
    """Clase base abstracta para todos los proveedores de OCR"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.is_available = False
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> bool:
        """Inicializar el proveedor (verificar credenciales, conectividad, etc.)"""
        pass
    
    @abstractmethod
    def process_image(
        self, 
        image: Image.Image, 
        language: str = 'es', 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Procesar imagen con OCR
        
        Args:
            image: Imagen PIL a procesar
            language: Código de idioma (es, en, etc.)
            **kwargs: Parámetros adicionales específicos del proveedor
            
        Returns:
            Dict con keys: success, text, confidence, processing_time, error_message
        """
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Obtener lista de idiomas soportados"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Probar conectividad y funcionamiento del proveedor"""
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Obtener información del proveedor"""
        return {
            'name': self.name,
            'available': self.is_available,
            'config': self.config,
            'supported_languages': self.get_supported_languages()
        }
    
    def validate_image(self, image: Image.Image) -> Dict[str, Any]:
        """Validar que la imagen es adecuada para OCR"""
        
        validation = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Verificar dimensiones mínimas
        if image.width < 100 or image.height < 100:
            validation['errors'].append('Imagen demasiado pequeña (mínimo 100x100)')
            validation['valid'] = False
        
        # Verificar dimensiones máximas
        if image.width > 5000 or image.height > 5000:
            validation['warnings'].append('Imagen muy grande, considerar reducir para mejor performance')
        
        # Verificar formato
        if image.mode not in ['RGB', 'L', 'RGBA']:
            validation['warnings'].append(f'Formato de imagen {image.mode} no optimal, mejor RGB o L')
        
        # Verificar aspecto
        aspect_ratio = image.width / image.height
        if aspect_ratio > 10 or aspect_ratio < 0.1:
            validation['warnings'].append('Relación de aspecto extrema detectada')
        
        return validation
    
    def preprocess_for_provider(self, image: Image.Image) -> Image.Image:
        """Preprocesamiento específico del proveedor (override si necesario)"""
        return image

class OCRResult:
    """Clase para estandarizar resultados de OCR"""
    
    def __init__(
        self,
        success: bool,
        text: str = "",
        confidence: float = 0.0,
        processing_time: float = 0.0,
        provider: str = "",
        language: str = "",
        error_message: str = None,
        raw_response: Any = None,
        metadata: Dict = None
    ):
        self.success = success
        self.text = text
        self.confidence = confidence
        self.processing_time = processing_time
        self.provider = provider
        self.language = language
        self.error_message = error_message
        self.raw_response = raw_response
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir resultado a diccionario"""
        return {
            'success': self.success,
            'text': self.text,
            'confidence': self.confidence,
            'processing_time': self.processing_time,
            'provider': self.provider,
            'language': self.language,
            'error_message': self.error_message,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OCRResult':
        """Crear resultado desde diccionario"""
        return cls(
            success=data.get('success', False),
            text=data.get('text', ''),
            confidence=data.get('confidence', 0.0),
            processing_time=data.get('processing_time', 0.0),
            provider=data.get('provider', ''),
            language=data.get('language', ''),
            error_message=data.get('error_message'),
            metadata=data.get('metadata', {})
        )

class OCROrchestrator:
    """Orquestador para manejar múltiples proveedores OCR con fallback"""
    
    def __init__(self):
        self.providers: List[OCRProvider] = []
        self.default_language = 'es'
        self.min_confidence_threshold = 0.7
    
    def register_provider(self, provider: OCRProvider):
        """Registrar un proveedor de OCR"""
        if provider.is_available:
            self.providers.append(provider)
            logger.info(f"Proveedor {provider.name} registrado y disponible")
        else:
            logger.warning(f"Proveedor {provider.name} no disponible")
    
    def get_available_providers(self) -> List[str]:
        """Obtener lista de proveedores disponibles"""
        return [provider.name for provider in self.providers if provider.is_available]
    
    async def process_with_fallback(
        self,
        image: Image.Image,
        language: str = None,
        max_attempts: int = None,
        **kwargs
    ) -> OCRResult:
        """
        Procesar imagen con sistema de fallback automático
        
        Args:
            image: Imagen a procesar
            language: Idioma (usa default si no se especifica)
            max_attempts: Máximo número de proveedores a intentar
            **kwargs: Parámetros adicionales
        """
        
        language = language or self.default_language
        max_attempts = max_attempts or len(self.providers)
        
        if not self.providers:
            return OCRResult(
                success=False,
                error_message="No hay proveedores de OCR disponibles"
            )
        
        last_error = "No se pudo procesar la imagen"
        
        for i, provider in enumerate(self.providers[:max_attempts]):
            try:
                logger.info(f"Intentando con proveedor {provider.name} (intento {i+1})")
                
                # Validar imagen para este proveedor
                validation = provider.validate_image(image)
                if not validation['valid']:
                    logger.warning(f"Imagen no válida para {provider.name}: {validation['errors']}")
                    continue
                
                # Preprocesar para este proveedor específico
                processed_image = provider.preprocess_for_provider(image)
                
                # Procesar con OCR
                result_dict = provider.process_image(processed_image, language, **kwargs)
                result = OCRResult(
                    **result_dict,
                    provider=provider.name,
                    language=language
                )
                
                # Verificar si el resultado es bueno
                if result.success and result.confidence >= self.min_confidence_threshold:
                    logger.info(f"OCR exitoso con {provider.name}: "
                               f"{result.confidence:.1f}% confianza")
                    return result
                
                elif result.success:
                    logger.info(f"OCR con {provider.name} tiene baja confianza: "
                               f"{result.confidence:.1f}%")
                    # Continuar con siguiente proveedor pero guardar este resultado
                    last_result = result
                
                else:
                    logger.warning(f"OCR falló con {provider.name}: {result.error_message}")
                    last_error = result.error_message
                
            except Exception as e:
                logger.error(f"Error con proveedor {provider.name}: {e}")
                last_error = str(e)
                continue
        
        # Si llegamos aquí, ningún proveedor tuvo éxito con alta confianza
        # Devolver el mejor resultado que tengamos, si existe
        if 'last_result' in locals():
            logger.warning(f"Devolviendo resultado de baja confianza: "
                          f"{last_result.confidence:.1f}%")
            return last_result
        
        # No hay resultados válidos
        return OCRResult(
            success=False,
            error_message=f"Todos los proveedores fallaron. Último error: {last_error}"
        )
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de los proveedores"""
        stats = {
            'total_providers': len(self.providers),
            'available_providers': len([p for p in self.providers if p.is_available]),
            'provider_info': [p.get_provider_info() for p in self.providers]
        }
        return stats

# Instancia global del orquestador
ocr_orchestrator = OCROrchestrator()