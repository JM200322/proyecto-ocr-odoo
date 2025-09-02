#!/usr/bin/env python3
"""
Proveedor OCR.Space - Implementación mejorada
"""

import time
import io
import requests
from PIL import Image, ImageOps, ImageFilter
import base64
from pathlib import Path
from typing import Dict, List, Any
import logging

from .base_provider import OCRProvider, OCRResult

logger = logging.getLogger(__name__)

class OCRSpaceProvider(OCRProvider):
    """Proveedor OCR usando OCR.Space API"""
    
    def __init__(self, api_key: str = "K86759595888957", config: Dict = None):
        self.api_key = api_key
        self.endpoint = "https://api.ocr.space/parse/image"
        
        default_config = {
            'max_retries': 3,
            'timeout': 60,
            'default_engine': 2,
            'max_file_size_mb': 1,
            'target_dpi': 300
        }
        
        if config:
            default_config.update(config)
        
        super().__init__("OCR.Space", default_config)
    
    def _initialize(self) -> bool:
        """Inicializar y verificar el proveedor"""
        try:
            if not self.api_key:
                logger.error("API key de OCR.Space no configurada")
                return False
            
            # Probar conectividad básica
            test_result = self.test_connection()
            self.is_available = test_result['success']
            
            if self.is_available:
                logger.info("OCR.Space proveedor inicializado correctamente")
            else:
                logger.error(f"Error inicializando OCR.Space: {test_result.get('error', 'Unknown')}")
            
            return self.is_available
            
        except Exception as e:
            logger.error(f"Error inicializando OCR.Space: {e}")
            return False
    
    def get_supported_languages(self) -> List[str]:
        """Idiomas soportados por OCR.Space"""
        return [
            'ara', 'bul', 'chs', 'cht', 'hrv', 'cze', 'dan', 'dut', 'eng', 
            'fin', 'fre', 'ger', 'gre', 'hun', 'kor', 'ita', 'jpn', 'pol', 
            'por', 'rus', 'slv', 'spa', 'swe', 'tur'
        ]
    
    def _map_language_code(self, language: str) -> str:
        """Mapear códigos de idioma estándar a códigos OCR.Space"""
        language_mapping = {
            'es': 'spa',
            'en': 'eng', 
            'fr': 'fre',
            'de': 'ger',
            'it': 'ita',
            'pt': 'por',
            'ru': 'rus',
            'ar': 'ara',
            'zh': 'chs',
            'ja': 'jpn',
            'ko': 'kor',
            'pl': 'pol',
            'sv': 'swe',
            'tr': 'tur',
            'nl': 'dut',
            'da': 'dan',
            'fi': 'fin',
            'el': 'gre',
            'hu': 'hun',
            'hr': 'hrv',
            'cs': 'cze',
            'bg': 'bul',
            'sl': 'slv'
        }
        
        # Si ya es un código OCR.Space válido, devolverlo tal cual
        if language in self.get_supported_languages():
            return language
            
        # Mapear código estándar a OCR.Space
        mapped_language = language_mapping.get(language.lower(), 'spa')
        logger.debug(f"Mapeando idioma '{language}' a '{mapped_language}'")
        return mapped_language
    
    def process_image(
        self, 
        image: Image.Image, 
        language: str = 'spa', 
        engine: int = None,
        digits_only: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Procesar imagen con OCR.Space"""
        
        start_time = time.time()
        engine = engine or self.config['default_engine']
        
        # Mapear código de idioma al formato OCR.Space
        mapped_language = self._map_language_code(language)
        logger.debug(f"Procesando imagen con idioma '{language}' -> '{mapped_language}'")
        
        try:
            # Validar imagen
            validation = self.validate_image(image)
            if not validation['valid']:
                return {
                    'success': False,
                    'text': '',
                    'confidence': 0,
                    'processing_time': 0,
                    'error_message': f"Imagen no válida: {validation['errors']}"
                }
            
            # Preprocesar imagen para OCR.Space
            if digits_only:
                processed_image = self._prepare_image_for_digits(image)
            else:
                processed_image = self._prepare_image_for_ocr_space(image)
            
            # Convertir a bytes
            img_buffer = io.BytesIO()
            processed_image.save(img_buffer, format='JPEG', quality=90, optimize=True)
            image_bytes = img_buffer.getvalue()
            
            # Verificar tamaño
            if len(image_bytes) > self.config['max_file_size_mb'] * 1024 * 1024:
                # Comprimir más agresivamente
                img_buffer = io.BytesIO()
                processed_image.save(img_buffer, format='JPEG', quality=70, optimize=True)
                image_bytes = img_buffer.getvalue()
            
            # Llamar a la API
            result = self._call_ocr_space_api(
                image_bytes, 
                mapped_language, 
                engine, 
                self.config['max_retries'], 
                self.config['timeout'],
                digits_only
            )
            
            result['processing_time'] = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"Error en OCR.Space: {e}")
            return {
                'success': False,
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'error_message': str(e)
            }
    
    def _prepare_image_for_ocr_space(self, image: Image.Image) -> Image.Image:
        """Preparar imagen específicamente para OCR.Space"""
        
        # Convertir a RGB si es necesario
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        
        # Optimizar resolución
        w, h = image.size
        max_dimension = 2200  # OCR.Space funciona bien con esta resolución
        
        if max(w, h) > max_dimension:
            scale = max_dimension / float(max(w, h))
            new_size = (int(w * scale), int(h * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Mejorar para OCR si la imagen es muy pequeña
        elif max(w, h) < 600:
            scale = 600 / float(max(w, h))
            new_size = (int(w * scale), int(h * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Aplicar preprocesamiento optimizado para OCR.Space
        if image.mode == "RGB":
            # Convertir a escala de grises con mejor contraste
            grayscale = ImageOps.grayscale(image)
            # Mejorar contraste
            enhanced = ImageOps.autocontrast(grayscale, cutoff=1)
            # Aplicar sharpen suave
            sharpened = enhanced.filter(ImageFilter.SHARPEN)
            # Convertir de vuelta a RGB para OCR.Space
            image = sharpened.convert("RGB")
        
        return image
    
    def _prepare_image_for_digits(self, image: Image.Image) -> Image.Image:
        """Preprocesamiento específico para reconocimiento de dígitos en medidores/displays"""
        
        # Convertir a RGB si es necesario
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        
        # Para medidores digitales, usar resolución más alta
        w, h = image.size
        target_height = 1200  # Resolución alta para dígitos pequeños
        
        if h < target_height:
            scale = target_height / float(h)
            new_size = (int(w * scale), int(h * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.debug(f"Imagen escalada para dígitos: {w}x{h} -> {new_size[0]}x{new_size[1]}")
        
        # Convertir a escala de grises para mejor contraste de dígitos
        grayscale = ImageOps.grayscale(image)
        
        # Aumentar contraste agresivamente para dígitos
        enhanced = ImageOps.autocontrast(grayscale, cutoff=2)
        
        # Aplicar filtro sharpen más fuerte para dígitos
        sharpened = enhanced.filter(ImageFilter.SHARPEN)
        sharpened = sharpened.filter(ImageFilter.SHARPEN)  # Doble sharpen
        
        # Aplicar umbralización para binarizar la imagen (blanco/negro puro)
        # Esto ayuda mucho con displays digitales
        import numpy as np
        img_array = np.array(sharpened)
        
        # Umbralización adaptativa (mejor para displays con diferentes brillos)
        threshold = np.mean(img_array)  # Umbral dinámico
        binary_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
        
        # Convertir de vuelta a PIL
        binary_image = Image.fromarray(binary_array, mode='L')
        
        # Convertir a RGB para OCR.Space
        result_image = binary_image.convert("RGB")
        
        logger.debug("Preprocesamiento para dígitos completado: binarización aplicada")
        return result_image
    
    def _extract_digits_only(self, text: str) -> str:
        """Extraer solo dígitos y puntos decimales del texto OCR"""
        import re
        
        if not text:
            return ""
        
        # Remover saltos de línea y espacios extras
        cleaned_text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Extraer números (incluyendo decimales y negativos)
        # Patrón: números enteros, decimales, con posibles espacios entre dígitos
        number_patterns = [
            r'-?\d+[.,]\d+',          # Decimales: 123.45 o 123,45
            r'-?\d+',                 # Enteros: 123
            r'\d+\s+\d+[.,]\d+',      # Con espacios: 1 234.56
            r'\d+\s+\d+',             # Con espacios: 1 234
        ]
        
        numbers = []
        for pattern in number_patterns:
            matches = re.findall(pattern, cleaned_text)
            numbers.extend(matches)
        
        # Si no encontramos números con patrones, extraer dígitos sueltos
        if not numbers:
            # Extraer solo dígitos, puntos y comas
            digits_only = re.findall(r'[\d.,\-\s]+', cleaned_text)
            if digits_only:
                # Limpiar espacios extra y unir
                cleaned_digits = ''.join(digits_only).strip()
                # Remover espacios internos pero mantener puntos/comas
                cleaned_digits = re.sub(r'\s+', '', cleaned_digits)
                numbers = [cleaned_digits] if cleaned_digits else []
        
        # Procesar y limpiar números encontrados
        processed_numbers = []
        for num in numbers:
            # Limpiar espacios
            num = re.sub(r'\s+', '', num)
            # Reemplazar comas por puntos para estándar decimal
            num = num.replace(',', '.')
            # Validar que es un número válido
            if re.match(r'^-?\d+\.?\d*$', num):
                processed_numbers.append(num)
        
        # Devolver el número más probable (el más largo o primero encontrado)
        if processed_numbers:
            # Ordenar por longitud (número más completo)
            processed_numbers.sort(key=len, reverse=True)
            result = processed_numbers[0]
            logger.debug(f"Números extraídos: {processed_numbers} -> seleccionado: '{result}'")
            return result
        
        # Como último recurso, extraer solo dígitos consecutivos
        digits_only = re.findall(r'\d+', text)
        if digits_only:
            result = ''.join(digits_only)
            logger.debug(f"Extrayendo solo dígitos consecutivos: '{result}'")
            return result
        
        logger.warning(f"No se pudieron extraer dígitos del texto: '{text}'")
        return ""
    
    def _call_ocr_space_api(
        self, 
        image_bytes: bytes, 
        language: str, 
        engine: int, 
        retries: int, 
        timeout: int,
        digits_only: bool = False
    ) -> Dict[str, Any]:
        """Llamar a la API de OCR.Space con reintentos"""
        
        data = {
            "apikey": self.api_key,
            "language": language,
            "isOverlayRequired": False,
            "OCREngine": engine,
            "detectOrientation": True,
            "scale": True,
        }
        
        # Configuración específica para reconocimiento de dígitos
        if digits_only:
            data["isTable"] = True  # Ayuda con formato tabular de números
            # OCR.Space no tiene un parámetro específico para solo dígitos
            # pero podemos optimizar otros parámetros
            data["detectOrientation"] = False  # Los medidores suelen estar bien orientados
            logger.debug("Configuración para reconocimiento de dígitos activada")
        
        backoff = 2
        
        for attempt in range(1, retries + 1):
            try:
                logger.debug(f"OCR.Space API llamada, intento {attempt}")
                
                response = requests.post(
                    self.endpoint,
                    data=data,
                    files={"filename": ("image.jpg", image_bytes, "application/octet-stream")},
                    timeout=timeout,
                )
                response.raise_for_status()
                payload = response.json()
                
                # Verificar errores de la API
                if payload.get("IsErroredOnProcessing"):
                    error_msg = payload.get("ErrorMessage") or payload.get("ErrorDetails") or "Unknown API error"
                    
                    # Asegurar que error_msg sea string
                    if isinstance(error_msg, list):
                        error_msg = str(error_msg)
                    elif not isinstance(error_msg, str):
                        error_msg = str(error_msg)
                    
                    # Si es error 500, intentar con motor alternativo
                    if "internal server error" in error_msg.lower() and engine == 2:
                        logger.warning(f"Error 500 con motor {engine}, probando motor 3...")
                        return self._call_ocr_space_api(image_bytes, language, 3, 1, timeout)
                    
                    raise RuntimeError(f"OCR.Space error: {error_msg}")
                
                # Procesar resultados
                results = payload.get("ParsedResults") or []
                if not results:
                    return {
                        "success": False,
                        "text": "",
                        "confidence": 0,
                        "error_message": "No se detectó texto en la imagen"
                    }
                
                parsed_result = results[0]
                text = parsed_result.get("ParsedText", "").strip()
                
                # Si es modo solo dígitos, filtrar el texto
                if digits_only:
                    original_text = text
                    text = self._extract_digits_only(text)
                    logger.debug(f"Filtrado de dígitos: '{original_text}' -> '{text}'")
                
                # Calcular confianza promedio si está disponible
                confidence = self._calculate_confidence(parsed_result)
                
                return {
                    "success": True,
                    "text": text,
                    "confidence": confidence,
                    "raw_response": payload
                }
                
            except requests.HTTPError as e:
                if e.response.status_code == 500:
                    logger.warning(f"Intento {attempt}/{retries}: Error 500 - reintentando...")
                    if attempt == retries:
                        return {
                            "success": False,
                            "text": "",
                            "confidence": 0,
                            "error_message": f"Error 500 persistente después de {retries} intentos"
                        }
                    time.sleep(backoff)
                    backoff *= 2
                    
                elif e.response.status_code == 429:
                    logger.warning(f"Rate limit alcanzado, esperando...")
                    if attempt == retries:
                        return {
                            "success": False,
                            "text": "",
                            "confidence": 0,
                            "error_message": "Rate limit alcanzado"
                        }
                    time.sleep(backoff * 2)
                    backoff *= 2
                    
                else:
                    return {
                        "success": False,
                        "text": "",
                        "confidence": 0,
                        "error_message": f"HTTP {e.response.status_code}: {e.response.text}"
                    }
                    
            except (requests.ConnectionError, requests.Timeout) as e:
                logger.warning(f"Intento {attempt}/{retries}: Error de conexión - reintentando...")
                if attempt == retries:
                    return {
                        "success": False,
                        "text": "",
                        "confidence": 0,
                        "error_message": f"Error de conectividad: {str(e)}"
                    }
                time.sleep(backoff)
                backoff *= 2
        
        return {
            "success": False,
            "text": "",
            "confidence": 0,
            "error_message": "Falló después de todos los reintentos"
        }
    
    def _calculate_confidence(self, parsed_result: Dict) -> float:
        """Calcular confianza promedio del resultado OCR"""
        
        # OCR.Space puede proporcionar información de confianza en TextOverlay
        overlay = parsed_result.get("TextOverlay", {})
        lines = overlay.get("Lines", [])
        
        if lines:
            confidences = []
            for line in lines:
                for word in line.get("Words", []):
                    if "Confidence" in word:
                        confidences.append(word["Confidence"])
            
            if confidences:
                return sum(confidences) / len(confidences)
        
        # Si no hay información de confianza, estimar basándose en el texto
        text = parsed_result.get("ParsedText", "")
        if not text:
            return 0.0
        
        # Estimación heurística de confianza
        confidence = 50.0  # Base
        
        # Bonificar por longitud razonable
        if 10 <= len(text) <= 1000:
            confidence += 20
        
        # Bonificar por presencia de palabras comunes
        common_words = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le']
        word_count = sum(1 for word in common_words if word in text.lower())
        confidence += min(word_count * 5, 20)
        
        # Penalizar muchos caracteres extraños
        weird_chars = sum(1 for c in text if ord(c) > 127 and c not in 'áéíóúüñÁÉÍÓÚÜÑ')
        if weird_chars > len(text) * 0.1:
            confidence -= 20
        
        return max(0.0, min(100.0, confidence))
    
    def test_connection(self) -> Dict[str, Any]:
        """Probar conexión con OCR.Space"""
        try:
            # Crear imagen de prueba muy simple
            test_img = Image.new('RGB', (100, 50), color='white')
            
            # Convertir a bytes
            img_buffer = io.BytesIO()
            test_img.save(img_buffer, format='JPEG', quality=90)
            image_bytes = img_buffer.getvalue()
            
            # Llamada de prueba con timeout corto
            result = self._call_ocr_space_api(image_bytes, "spa", 2, 1, 10)
            
            return {
                'success': True,
                'message': 'OCR.Space conectado correctamente',
                'api_responsive': result.get('success', False),
                'test_details': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error conectando con OCR.Space: {str(e)}',
                'error': str(e)
            }
    
    def preprocess_for_provider(self, image: Image.Image) -> Image.Image:
        """Preprocesamiento específico para OCR.Space"""
        return self._prepare_image_for_ocr_space(image)

# Función de conveniencia para crear instancia
def create_ocr_space_provider(api_key: str = None, **config) -> OCRSpaceProvider:
    """Crear instancia de OCRSpaceProvider"""
    api_key = api_key or "K86759595888957"  # API key por defecto
    return OCRSpaceProvider(api_key, config)