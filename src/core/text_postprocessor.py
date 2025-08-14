#!/usr/bin/env python3
"""
Módulo de post-procesamiento inteligente de texto extraído por OCR
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
import unicodedata

logger = logging.getLogger(__name__)

class TextPostprocessor:
    """Clase para post-procesamiento inteligente de texto OCR"""
    
    def __init__(self):
        self.correction_patterns = self._load_correction_patterns()
        self.confidence_rules = self._load_confidence_rules()
    
    def _load_correction_patterns(self) -> Dict[str, str]:
        """Cargar patrones de corrección comunes de OCR"""
        return {
            # Números confundidos con letras en contexto de letras
            r'\b([A-Za-záéíóúüñ]+)0([A-Za-záéíóúüñ]+)\b': r'\1O\2',
            r'\b([A-Za-záéíóúüñ]+)1([A-Za-záéíóúüñ]+)\b': r'\1I\2',
            r'\b([A-Za-záéíóúüñ]+)5([A-Za-záéíóúüñ]+)\b': r'\1S\2',
            r'\b([A-Za-záéíóúüñ]+)8([A-Za-záéíóúüñ]+)\b': r'\1B\2',
            r'\b([A-Za-záéíóúüñ]+)6([A-Za-záéíóúüñ]+)\b': r'\1G\2',
            
            # Letras confundidas con números en contexto numérico
            r'\b(\d+)O(\d+)\b': r'\g<1>0\g<2>',
            r'\b(\d+)I(\d+)\b': r'\g<1>1\g<2>',
            r'\b(\d+)S(\d+)\b': r'\g<1>5\g<2>',
            r'\b(\d+)B(\d+)\b': r'\g<1>8\g<2>',
            
            # Caracteres especiales comunes
            r'\|': 'I',
            r'`': "'",
            r'´': "'",
            r''': "'",
            r''': "'",
            r'"': '"',
            r'"': '"',
            r'°': 'o',
            r'¢': 'c',
            r'£': 'E',
            
            # Espacios antes de puntuación
            r'\s+([,.;:!?])': r'\1',
            
            # Espacios después de paréntesis de apertura y antes de cierre
            r'\(\s+': '(',
            r'\s+\)': ')',
            r'\[\s+': '[',
            r'\s+\]': ']',
            
            # Múltiples espacios
            r'\s+': ' ',
            
            # Líneas vacías múltiples
            r'\n\s*\n\s*\n': '\n\n',
        }
    
    def _load_confidence_rules(self) -> List[Dict]:
        """Cargar reglas para evaluar confianza del texto"""
        return [
            {
                'pattern': r'\d+',
                'weight': 0.1,
                'description': 'Contiene números'
            },
            {
                'pattern': r'[A-Z][a-z]+',
                'weight': 0.2,
                'description': 'Palabras capitalizadas'
            },
            {
                'pattern': r'\b[a-zA-Z]{3,}\b',
                'weight': 0.3,
                'description': 'Palabras de 3+ letras'
            },
            {
                'pattern': r'[,.;:!?]',
                'weight': 0.1,
                'description': 'Puntuación correcta'
            },
            {
                'pattern': r'\b(el|la|de|en|y|a|un|una|con|por|para|como|su|del|al)\b',
                'weight': 0.2,
                'description': 'Palabras comunes en español'
            }
        ]
    
    def process_advanced(self, text: str, language: str = 'es', document_type: str = 'general') -> Dict:
        """Post-procesamiento avanzado del texto extraído"""
        
        if not text:
            return {
                'text': '',
                'confidence_score': 0.0,
                'corrections_applied': 0,
                'quality_metrics': {},
                'detected_elements': {}
            }
        
        original_length = len(text)
        corrections_count = 0
        
        # Paso 1: Limpieza básica
        cleaned_text = self._basic_cleanup(text)
        
        # Paso 2: Correcciones específicas por idioma
        corrected_text, corrections = self._apply_language_corrections(cleaned_text, language)
        corrections_count += corrections
        
        # Paso 3: Correcciones específicas por tipo de documento
        specialized_text, spec_corrections = self._apply_document_corrections(corrected_text, document_type)
        corrections_count += spec_corrections
        
        # Paso 4: Análisis de calidad
        quality_metrics = self._analyze_quality(specialized_text)
        
        # Paso 5: Detección de elementos estructurados
        detected_elements = self._detect_structured_elements(specialized_text)
        
        # Paso 6: Cálculo de confianza
        confidence_score = self._calculate_confidence(specialized_text, quality_metrics)
        
        # Limpieza final
        final_text = specialized_text.strip()
        
        logger.info(f"Post-procesamiento: {original_length} -> {len(final_text)} caracteres, "
                   f"{corrections_count} correcciones, confianza: {confidence_score:.2f}")
        
        return {
            'text': final_text,
            'confidence_score': confidence_score,
            'corrections_applied': corrections_count,
            'quality_metrics': quality_metrics,
            'detected_elements': detected_elements,
            'length_change': len(final_text) - original_length
        }
    
    def _basic_cleanup(self, text: str) -> str:
        """Limpieza básica del texto"""
        
        # Normalizar Unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Eliminar líneas vacías múltiples
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
        
        # Aplicar patrones de corrección básicos
        for pattern, replacement in self.correction_patterns.items():
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def _apply_language_corrections(self, text: str, language: str) -> Tuple[str, int]:
        """Aplicar correcciones específicas del idioma"""
        corrections = 0
        
        if language == 'es':
            # Correcciones específicas para español
            spanish_corrections = {
                r'\bñ\b': 'ñ',  # Corregir ñ aislada
                r'\bÑ\b': 'Ñ',
                r'([aeiou])n([aeiou])': r'\1ñ\2',  # Posibles ñ perdidas
                r'\bque\b': 'que',  # Palabra muy común
                r'\bdel\b': 'del',
                r'\bcon\b': 'con',
                r'\bpor\b': 'por',
                r'\bpara\b': 'para',
            }
            
            for pattern, replacement in spanish_corrections.items():
                old_text = text
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                if text != old_text:
                    corrections += 1
        
        elif language == 'en':
            # Correcciones específicas para inglés
            english_corrections = {
                r'\bthe\b': 'the',
                r'\band\b': 'and',
                r'\bwith\b': 'with',
                r'\bfrom\b': 'from',
                r'\bthis\b': 'this',
                r'\bthat\b': 'that',
            }
            
            for pattern, replacement in english_corrections.items():
                old_text = text
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                if text != old_text:
                    corrections += 1
        
        return text, corrections
    
    def _apply_document_corrections(self, text: str, document_type: str) -> Tuple[str, int]:
        """Aplicar correcciones específicas por tipo de documento"""
        corrections = 0
        
        if document_type == 'invoice':
            # Correcciones para facturas
            invoice_patterns = {
                r'\bfACTURA\b': 'FACTURA',
                r'\bfactura\b': 'factura',
                r'\bTOTAL\b': 'TOTAL',
                r'\bIVA\b': 'IVA',
                r'\bSUBTOTAL\b': 'SUBTOTAL',
                r'(\d+)[.,](\d{2})\s*€': r'\1,\2 €',  # Formato de moneda
                r'(\d+)[.,](\d{2})\s*\$': r'\1.\2 $',
            }
            
            for pattern, replacement in invoice_patterns.items():
                old_text = text
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                if text != old_text:
                    corrections += 1
        
        elif document_type == 'contact':
            # Correcciones para información de contacto
            contact_patterns = {
                r'\bTEL[EF]ONO\b': 'TELÉFONO',
                r'\bEMAIL\b': 'EMAIL',
                r'\bDIRECCION\b': 'DIRECCIÓN',
                r'(\d{3})\s*(\d{3})\s*(\d{3})': r'\1 \2 \3',  # Formato teléfono
                r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})': 
                    lambda m: m.group(0).lower(),  # Email en minúsculas
            }
            
            for pattern, replacement in contact_patterns.items():
                old_text = text
                if callable(replacement):
                    text = re.sub(pattern, replacement, text)
                else:
                    text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                if text != old_text:
                    corrections += 1
        
        return text, corrections
    
    def _analyze_quality(self, text: str) -> Dict:
        """Analizar la calidad del texto extraído"""
        
        if not text:
            return {'words': 0, 'chars': 0, 'lines': 0, 'avg_word_length': 0}
        
        words = re.findall(r'\b\w+\b', text)
        lines = text.split('\n')
        
        metrics = {
            'words': len(words),
            'chars': len(text),
            'lines': len(lines),
            'avg_word_length': sum(len(word) for word in words) / max(len(words), 1),
            'has_numbers': bool(re.search(r'\d', text)),
            'has_punctuation': bool(re.search(r'[,.;:!?]', text)),
            'has_uppercase': bool(re.search(r'[A-Z]', text)),
            'has_lowercase': bool(re.search(r'[a-z]', text)),
            'special_chars_ratio': len(re.findall(r'[^\w\s]', text)) / max(len(text), 1),
            'digit_ratio': len(re.findall(r'\d', text)) / max(len(text), 1),
            'space_ratio': len(re.findall(r'\s', text)) / max(len(text), 1)
        }
        
        return metrics
    
    def _detect_structured_elements(self, text: str) -> Dict:
        """Detectar elementos estructurados en el texto"""
        
        elements = {
            'emails': re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text),
            'phones': re.findall(r'\b(?:\+34|0034)?\s*(?:6|7|8|9)\d{8}\b', text),
            'dates': re.findall(r'\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b', text),
            'amounts': re.findall(r'\b\d+[.,]\d{2}\s*[€$]\b', text),
            'postal_codes': re.findall(r'\b\d{5}\b', text),
            'dni_nie': re.findall(r'\b\d{8}[A-Za-z]\b', text),
            'urls': re.findall(r'https?://[^\s]+', text),
            'iban': re.findall(r'\bES\d{22}\b', text),
        }
        
        # Filtrar elementos vacíos
        elements = {k: v for k, v in elements.items() if v}
        
        return elements
    
    def _calculate_confidence(self, text: str, quality_metrics: Dict) -> float:
        """Calcular puntuación de confianza del texto"""
        
        if not text:
            return 0.0
        
        confidence = 0.0
        
        # Aplicar reglas de confianza
        for rule in self.confidence_rules:
            matches = len(re.findall(rule['pattern'], text, re.IGNORECASE))
            if matches > 0:
                confidence += rule['weight'] * min(matches / 10, 1.0)
        
        # Penalizar texto muy corto
        if len(text) < 10:
            confidence *= 0.5
        
        # Bonificar texto con buena estructura
        if quality_metrics.get('has_punctuation', False):
            confidence += 0.1
        
        if quality_metrics.get('has_uppercase', False) and quality_metrics.get('has_lowercase', False):
            confidence += 0.1
        
        # Penalizar demasiados caracteres especiales
        if quality_metrics.get('special_chars_ratio', 0) > 0.3:
            confidence *= 0.7
        
        # Normalizar a 0-1
        confidence = min(confidence, 1.0)
        
        return confidence
    
    def extract_key_value_pairs(self, text: str) -> Dict[str, str]:
        """Extraer pares clave-valor del texto"""
        
        pairs = {}
        
        # Patrones comunes de clave-valor
        patterns = [
            r'([A-Za-záéíóúüñÁÉÍÓÚÜÑ\s]+):\s*([^\n]+)',  # Clave: Valor
            r'([A-Za-záéíóúüñÁÉÍÓÚÜÑ\s]+)\s*:\s*([^\n]+)',  # Clave : Valor
            r'([A-Za-záéíóúüñÁÉÍÓÚÜÑ\s]+)\s+([A-Za-z0-9@.\-]+)',  # Nombre Email/Teléfono
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for key, value in matches:
                key = key.strip().lower()
                value = value.strip()
                
                # Filtrar claves muy cortas o valores vacíos
                if len(key) > 2 and len(value) > 0:
                    pairs[key] = value
        
        return pairs

# Instancia global del post-procesador
text_postprocessor = TextPostprocessor()