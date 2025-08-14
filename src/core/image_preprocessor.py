#!/usr/bin/env python3
"""
Módulo de preprocesamiento avanzado de imágenes para OCR
"""

import cv2
import numpy as np
import logging
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """Clase para preprocesamiento avanzado de imágenes"""
    
    def __init__(self):
        self.default_params = {
            'brightness': 0,
            'contrast': 100,
            'sharpness': 0,
            'denoise': True,
            'adaptive_threshold': True,
            'morphological_ops': True,
            'min_dpi': 300
        }
    
    def preprocess_advanced(self, image: Image.Image, **params) -> Image.Image:
        """Preprocesamiento avanzado de imagen para OCR de máxima precisión"""
        try:
            # Combinar parámetros por defecto con los proporcionados
            config = {**self.default_params, **params}
            
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            logger.info(f"Imagen original: {image.size}, modo: {image.mode}")
            
            # Aplicar ajustes básicos
            image = self._apply_basic_adjustments(image, config)
            
            # Convertir a array de OpenCV para procesamiento avanzado
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Procesamiento con OpenCV
            cv_image = self._opencv_processing(cv_image, config)
            
            # Convertir de vuelta a PIL
            processed_image = Image.fromarray(cv_image)
            
            # Redimensionar si es necesario
            processed_image = self._ensure_min_resolution(processed_image, config['min_dpi'])
            
            logger.info("Preprocesamiento completado")
            return processed_image
            
        except Exception as e:
            logger.error(f"Error en preprocesamiento: {e}")
            return image
    
    def _apply_basic_adjustments(self, image: Image.Image, config: dict) -> Image.Image:
        """Aplicar ajustes básicos de brillo, contraste y nitidez"""
        
        # Brillo
        if config['brightness'] != 0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1 + config['brightness'] / 100)
            logger.debug(f"Brillo ajustado: {config['brightness']}")
        
        # Contraste
        if config['contrast'] != 100:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(config['contrast'] / 100)
            logger.debug(f"Contraste ajustado: {config['contrast']}%")
        
        # Nitidez
        if config['sharpness'] > 0:
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1 + config['sharpness'] / 100)
            logger.debug(f"Nitidez aplicada: {config['sharpness']}")
        
        return image
    
    def _opencv_processing(self, cv_image: np.ndarray, config: dict) -> np.ndarray:
        """Procesamiento avanzado con OpenCV"""
        
        # Reducción de ruido
        if config['denoise']:
            cv_image = cv2.bilateralFilter(cv_image, 9, 75, 75)
            logger.debug("Reducción de ruido aplicada")
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Umbralización adaptativa
        if config['adaptive_threshold']:
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            logger.debug("Umbralización adaptativa aplicada")
        else:
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Operaciones morfológicas
        if config['morphological_ops']:
            kernel = np.ones((1, 1), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            logger.debug("Operaciones morfológicas aplicadas")
        
        return thresh
    
    def _ensure_min_resolution(self, image: Image.Image, min_dpi: int) -> Image.Image:
        """Asegurar resolución mínima para OCR óptimo"""
        
        if image.width < 1000 or image.height < 1000:
            scale_factor = max(1000 / image.width, 1000 / image.height)
            new_size = (
                int(image.width * scale_factor),
                int(image.height * scale_factor)
            )
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.debug(f"Imagen redimensionada a: {new_size}")
        
        return image
    
    def detect_document_bounds(self, image: Image.Image) -> Optional[Tuple[int, int, int, int]]:
        """Detectar los límites de un documento en la imagen"""
        try:
            # Convertir a OpenCV
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detectar bordes
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Encontrar el contorno más grande (probablemente el documento)
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Obtener bounding box
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Verificar que el área sea significativa
                image_area = image.width * image.height
                contour_area = w * h
                
                if contour_area > image_area * 0.1:  # Al menos 10% de la imagen
                    return (x, y, x + w, y + h)
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando límites del documento: {e}")
            return None
    
    def correct_perspective(self, image: Image.Image, corners: np.ndarray) -> Image.Image:
        """Corregir perspectiva del documento usando 4 puntos de esquina"""
        try:
            # Convertir a OpenCV
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Definir puntos de destino (rectángulo)
            width = int(max(np.linalg.norm(corners[0] - corners[1]), 
                           np.linalg.norm(corners[2] - corners[3])))
            height = int(max(np.linalg.norm(corners[1] - corners[2]), 
                            np.linalg.norm(corners[3] - corners[0])))
            
            dst_points = np.array([
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1]
            ], dtype=np.float32)
            
            # Calcular matriz de transformación
            matrix = cv2.getPerspectiveTransform(corners.astype(np.float32), dst_points)
            
            # Aplicar transformación
            corrected = cv2.warpPerspective(cv_image, matrix, (width, height))
            
            # Convertir de vuelta a PIL
            return Image.fromarray(cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB))
            
        except Exception as e:
            logger.error(f"Error corrigiendo perspectiva: {e}")
            return image
    
    def optimize_for_ocr(self, image: Image.Image, document_type: str = 'general') -> Image.Image:
        """Optimizar imagen según el tipo de documento"""
        
        # Perfiles de optimización por tipo de documento
        profiles = {
            'text': {
                'brightness': 10,
                'contrast': 120,
                'sharpness': 20,
                'denoise': True,
                'adaptive_threshold': True
            },
            'handwriting': {
                'brightness': 5,
                'contrast': 110,
                'sharpness': 10,
                'denoise': False,
                'adaptive_threshold': True
            },
            'invoice': {
                'brightness': 15,
                'contrast': 130,
                'sharpness': 25,
                'denoise': True,
                'adaptive_threshold': True
            },
            'general': {
                'brightness': 0,
                'contrast': 100,
                'sharpness': 0,
                'denoise': True,
                'adaptive_threshold': True
            }
        }
        
        profile = profiles.get(document_type, profiles['general'])
        return self.preprocess_advanced(image, **profile)

# Instancia global del preprocesador
image_preprocessor = ImagePreprocessor()