#!/usr/bin/env python3
"""
Proveedor Tesseract - Fallback local
"""

import time
import io
import subprocess
import tempfile
import os
from PIL import Image
from typing import Dict, List, Any
import logging

from .base_provider import OCRProvider

logger = logging.getLogger(__name__)

class TesseractProvider(OCRProvider):
    """Proveedor OCR usando Tesseract local como fallback"""
    
    def __init__(self, tesseract_path: str = None, config: Dict = None):
        self.tesseract_path = tesseract_path or self._find_tesseract()
        
        default_config = {
            'psm': 6,  # Page segmentation mode
            'oem': 3,  # OCR Engine mode
            'timeout': 30,
            'temp_cleanup': True
        }
        
        if config:
            default_config.update(config)
        
        super().__init__("Tesseract", default_config)
    
    def _find_tesseract(self) -> str:
        """Buscar instalación de Tesseract en el sistema"""
        possible_paths = [
            'tesseract',  # En PATH
            'C:/Program Files/Tesseract-OCR/tesseract.exe',  # Windows
            'C:/Program Files (x86)/Tesseract-OCR/tesseract.exe',  # Windows x86
            '/usr/bin/tesseract',  # Linux
            '/usr/local/bin/tesseract',  # macOS
            '/opt/homebrew/bin/tesseract',  # macOS Apple Silicon
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"Tesseract encontrado en: {path}")
                    return path
            except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None
    
    def _initialize(self) -> bool:
        """Inicializar y verificar Tesseract"""
        try:
            if not self.tesseract_path:
                logger.warning("Tesseract no encontrado en el sistema")
                return False
            
            # Verificar que Tesseract funciona
            result = subprocess.run(
                [self.tesseract_path, '--version'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                version_info = result.stdout.strip()
                logger.info(f"Tesseract disponible: {version_info.split()[1] if len(version_info.split()) > 1 else 'version unknown'}")
                self.is_available = True
                return True
            else:
                logger.error(f"Tesseract no responde correctamente: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error inicializando Tesseract: {e}")
            return False
    
    def get_supported_languages(self) -> List[str]:
        """Obtener idiomas soportados por Tesseract"""
        if not self.tesseract_path:
            return []
        
        try:
            result = subprocess.run(
                [self.tesseract_path, '--list-langs'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                # Primera línea es cabecera, el resto son idiomas
                lines = result.stdout.strip().split('\n')[1:]
                return [lang.strip() for lang in lines if lang.strip()]
            else:
                # Idiomas comunes por defecto
                return ['eng', 'spa', 'fra', 'deu', 'ita', 'por']
                
        except Exception as e:
            logger.warning(f"No se pudieron obtener idiomas de Tesseract: {e}")
            return ['eng', 'spa']
    
    def process_image(
        self, 
        image: Image.Image, 
        language: str = 'spa', 
        **kwargs
    ) -> Dict[str, Any]:
        """Procesar imagen con Tesseract"""
        
        start_time = time.time()
        temp_files = []
        
        try:
            # Mapear códigos de idioma
            lang_map = {
                'es': 'spa', 'spa': 'spa',
                'en': 'eng', 'eng': 'eng',
                'fr': 'fra', 'fra': 'fra',
                'de': 'deu', 'deu': 'deu',
                'it': 'ita', 'ita': 'ita',
                'pt': 'por', 'por': 'por'
            }
            
            tesseract_lang = lang_map.get(language, 'eng')
            
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
            
            # Preparar imagen para Tesseract
            processed_image = self._prepare_image_for_tesseract(image)
            
            # Crear archivo temporal para la imagen
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img:
                processed_image.save(temp_img.name, 'PNG')
                temp_files.append(temp_img.name)
                
                # Crear archivo temporal para la salida
                with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_out:
                    temp_files.append(temp_out.name)
                    output_base = temp_out.name[:-4]  # Sin extensión
                
                # Construir comando Tesseract
                cmd = [
                    self.tesseract_path,
                    temp_img.name,
                    output_base,
                    '-l', tesseract_lang,
                    '--psm', str(self.config['psm']),
                    '--oem', str(self.config['oem'])
                ]
                
                # Ejecutar Tesseract
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.config['timeout']
                )
                
                if result.returncode == 0:
                    # Leer texto extraído
                    output_file = output_base + '.txt'
                    if os.path.exists(output_file):
                        with open(output_file, 'r', encoding='utf-8') as f:
                            text = f.read().strip()
                        temp_files.append(output_file)
                        
                        # Calcular confianza estimada
                        confidence = self._estimate_confidence(text, processed_image)
                        
                        return {
                            'success': True,
                            'text': text,
                            'confidence': confidence,
                            'processing_time': time.time() - start_time,
                            'metadata': {
                                'tesseract_version': self._get_version(),
                                'language_used': tesseract_lang,
                                'psm': self.config['psm'],
                                'oem': self.config['oem']
                            }
                        }
                    else:
                        return {
                            'success': False,
                            'text': '',
                            'confidence': 0,
                            'processing_time': time.time() - start_time,
                            'error_message': 'Tesseract no generó archivo de salida'
                        }
                else:
                    return {
                        'success': False,
                        'text': '',
                        'confidence': 0,
                        'processing_time': time.time() - start_time,
                        'error_message': f'Tesseract error: {result.stderr}'
                    }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'error_message': f'Tesseract timeout después de {self.config["timeout"]}s'
            }
        
        except Exception as e:
            return {
                'success': False,
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'error_message': f'Error en Tesseract: {str(e)}'
            }
        
        finally:
            # Limpiar archivos temporales
            if self.config['temp_cleanup']:
                for temp_file in temp_files:
                    try:
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)
                    except Exception as e:
                        logger.warning(f"No se pudo limpiar archivo temporal {temp_file}: {e}")
    
    def _prepare_image_for_tesseract(self, image: Image.Image) -> Image.Image:
        """Preparar imagen específicamente para Tesseract"""
        
        # Convertir a escala de grises si no lo está
        if image.mode != 'L':
            image = image.convert('L')
        
        # Redimensionar si es muy pequeña
        if image.width < 300 or image.height < 300:
            scale = max(300 / image.width, 300 / image.height)
            new_size = (int(image.width * scale), int(image.height * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Redimensionar si es muy grande (Tesseract puede ser lento)
        elif image.width > 3000 or image.height > 3000:
            scale = min(3000 / image.width, 3000 / image.height)
            new_size = (int(image.width * scale), int(image.height * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image
    
    def _estimate_confidence(self, text: str, image: Image.Image) -> float:
        """Estimar confianza del resultado Tesseract"""
        
        if not text:
            return 0.0
        
        confidence = 50.0  # Base
        
        # Factores que aumentan confianza
        if len(text) > 10:
            confidence += 10
        
        # Presencia de palabras comunes
        common_spanish = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se']
        word_matches = sum(1 for word in common_spanish if word in text.lower())
        confidence += min(word_matches * 3, 15)
        
        # Relación texto/imagen razonable
        char_density = len(text) / (image.width * image.height / 1000)
        if 0.1 <= char_density <= 10:
            confidence += 10
        
        # Penalizar caracteres extraños
        weird_chars = sum(1 for c in text if ord(c) > 127 and c not in 'áéíóúüñÁÉÍÓÚÜÑ¿¡')
        if weird_chars > len(text) * 0.2:
            confidence -= 20
        
        # Penalizar líneas muy cortas (posibles errores)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        short_lines = sum(1 for line in lines if len(line) < 3)
        if short_lines > len(lines) * 0.5:
            confidence -= 15
        
        return max(0.0, min(100.0, confidence))
    
    def _get_version(self) -> str:
        """Obtener versión de Tesseract"""
        try:
            result = subprocess.run(
                [self.tesseract_path, '--version'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.split('\n')[0].strip()
        except:
            pass
        return "unknown"
    
    def test_connection(self) -> Dict[str, Any]:
        """Probar Tesseract"""
        if not self.tesseract_path:
            return {
                'success': False,
                'message': 'Tesseract no está instalado o no se encuentra en PATH'
            }
        
        try:
            # Crear imagen de prueba
            test_img = Image.new('L', (200, 100), color=255)
            
            # Procesar con Tesseract
            result = self.process_image(test_img, 'eng')
            
            return {
                'success': True,
                'message': 'Tesseract funcionando correctamente',
                'version': self._get_version(),
                'test_result': result.get('success', False),
                'supported_languages': len(self.get_supported_languages())
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error probando Tesseract: {str(e)}'
            }

# Función de conveniencia
def create_tesseract_provider(tesseract_path: str = None, **config) -> TesseractProvider:
    """Crear instancia de TesseractProvider"""
    return TesseractProvider(tesseract_path, config)