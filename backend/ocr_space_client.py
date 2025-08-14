# backend/ocr_space_client.py
import time
import io
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from PIL import Image, ImageOps, ImageFilter
import base64

logger = logging.getLogger(__name__)

class OCRSpaceClient:
    def __init__(self, api_key: str = "K86759595888957"):
        self.api_key = api_key
        self.endpoint = "https://api.ocr.space/parse/image"
        
    def load_and_prepare(self, image_path: Path, max_px: int = 2200, target_size_kb: int = 900) -> bytes:
        """Carga imagen, la normaliza a RGB, elimina alpha, redimensiona y comprime <= ~1MB."""
        if not image_path.exists():
            raise FileNotFoundError(f"No existe: {image_path}")

        img = Image.open(image_path)
        img.load()

        # Convertir a RGB (evita CMYK/alpha)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Escala si el lado largo excede max_px
        w, h = img.size
        m = max(w, h)
        if m > max_px:
            scale = max_px / float(m)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        # Preprocesado suave: grises + contraste + sharpen
        g = ImageOps.grayscale(img)
        g = ImageOps.autocontrast(g)
        g = g.filter(ImageFilter.SHARPEN)

        # Guardar a JPEG o PNG optimizado intentando < target_size_kb
        # 1) intenta JPEG (suele pesar menos)
        for quality in (90, 85, 80, 75, 70):
            buf = io.BytesIO()
            g.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
            if buf.tell() <= target_size_kb * 1024:
                return buf.getvalue()

        # 2) fallback a PNG optimizado
        buf = io.BytesIO()
        g.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    def ocr_space_image(self, image_bytes: bytes, language: str = "spa", engine: int = 2, retries: int = 3, timeout: int = 60) -> Dict[str, Any]:
        """Llama OCR.Space con reintentos exponenciales y retorna resultado completo."""
        data = {
            "apikey": self.api_key,
            "language": language,
            "isOverlayRequired": False,
            "OCREngine": engine,           # 1/2/3, prueba 2 o 3
            "detectOrientation": True,
            "scale": True,                 # mejora reconocimiento
        }

        backoff = 2
        for attempt in range(1, retries + 1):
            try:
                r = requests.post(
                    self.endpoint,
                    data=data,
                    files={"filename": ("image.jpg", image_bytes, "application/octet-stream")},
                    timeout=timeout,
                )
                r.raise_for_status()
                payload = r.json()

                # Manejo de errores explícitos de la API
                if payload.get("IsErroredOnProcessing"):
                    # Devuelve mensaje lo más explícito posible
                    err = payload.get("ErrorMessage") or payload.get("ErrorDetails") or "Unknown error"
                    # Si te pasa seguido, prueba OCREngine=3
                    raise RuntimeError(f"OCR.Space error: {err}")

                results = payload.get("ParsedResults") or []
                if not results:
                    return {
                        "text": "",
                        "confidence": 0,
                        "processing_time": 0,
                        "success": False,
                        "message": "No se detectó texto"
                    }

                parsed_result = results[0]
                text = parsed_result.get("ParsedText", "")
                confidence = parsed_result.get("TextOverlay", {}).get("Lines", [])
                
                # Calcular confianza promedio si está disponible
                avg_confidence = 0
                if confidence:
                    confidences = []
                    for line in confidence:
                        for word in line.get("Words", []):
                            if "Confidence" in word:
                                confidences.append(word["Confidence"])
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

                return {
                    "text": text,
                    "confidence": avg_confidence,
                    "processing_time": float(payload.get("ProcessingTimeInMilliseconds", 0)) / 1000,
                    "success": True,
                    "message": "OCR completado exitosamente",
                    "raw_response": payload
                }

            except requests.HTTPError as e:
                # Manejar errores HTTP específicos
                if e.response.status_code == 500:
                    logger.warning(f"Intento {attempt}/{retries}: Error 500 del servidor OCR.Space - reintentando...")
                    if attempt == retries:
                        raise RuntimeError(f"Error 500 persistente del servidor OCR.Space después de {retries} intentos. El servicio puede estar sobrecargado.")
                    time.sleep(backoff)
                    backoff *= 2
                elif e.response.status_code == 429:
                    logger.warning(f"Intento {attempt}/{retries}: Rate limit alcanzado - esperando más tiempo...")
                    if attempt == retries:
                        raise RuntimeError("Rate limit alcanzado. Demasiadas solicitudes a OCR.Space.")
                    time.sleep(backoff * 2)  # Esperar más tiempo para rate limits
                    backoff *= 2
                else:
                    logger.error(f"Error HTTP {e.response.status_code}: {e.response.text}")
                    raise
            except (requests.ConnectionError, requests.Timeout) as e:
                logger.warning(f"Intento {attempt}/{retries}: Error de conexión - reintentando...")
                if attempt == retries:
                    raise
                time.sleep(backoff)
                backoff *= 2  # retry exponencial

    def process_image_from_path(self, image_path: str, language: str = "spa", engine: int = 2) -> Dict[str, Any]:
        """Procesar imagen desde ruta de archivo"""
        path = Path(image_path).resolve()
        try:
            image_bytes = self.load_and_prepare(path)
            result = self.ocr_space_image(image_bytes, language=language, engine=engine)
            logger.info(f"OCR completado: {len(result['text'])} caracteres, {result['confidence']:.1f}% confianza")
            return result
        except FileNotFoundError as e:
            logger.error(f"[Ruta inválida] {e}")
            return {"success": False, "message": str(e)}
        except RuntimeError as e:
            logger.error(f"[API] {e}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"[Error] {e}")
            return {"success": False, "message": str(e)}

    def process_image_from_base64(self, base64_data: str, language: str = "spa", engine: int = 2) -> Dict[str, Any]:
        """Procesar imagen desde datos base64"""
        try:
            # Decodificar base64
            if ',' in base64_data:
                image_data = base64.b64decode(base64_data.split(',')[1])
            else:
                image_data = base64.b64decode(base64_data)
            
            # Crear imagen PIL desde bytes
            img = Image.open(io.BytesIO(image_data))
            
            # Guardar temporalmente para procesar
            temp_path = Path("temp_image.jpg")
            img.save(temp_path, "JPEG", quality=90)
            
            # Procesar
            result = self.process_image_from_path(str(temp_path), language, engine)
            
            # Limpiar archivo temporal
            temp_path.unlink(missing_ok=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error procesando imagen base64: {e}")
            return {"success": False, "message": str(e)}

    def process_image_from_bytes(self, image_bytes: bytes, language: str = "spa", engine: int = 2) -> Dict[str, Any]:
        """Procesar imagen desde bytes directamente con fallback a diferentes motores"""
        try:
            # Crear imagen PIL desde bytes
            img = Image.open(io.BytesIO(image_bytes))
            
            # Guardar temporalmente para procesar
            temp_path = Path("temp_image.jpg")
            img.save(temp_path, "JPEG", quality=90)
            
            # Intentar con el motor especificado
            result = self.process_image_from_path(str(temp_path), language, engine)
            
            # Si falla con error 500, intentar con motor alternativo
            if not result["success"] and "Error 500" in result.get("message", ""):
                logger.info("🔄 Error 500 detectado, probando con motor alternativo...")
                
                # Probar con motor alternativo
                alternative_engine = 3 if engine == 2 else 2
                logger.info(f"🔄 Probando con motor OCR {alternative_engine}...")
                
                try:
                    result = self.process_image_from_path(str(temp_path), language, alternative_engine)
                    if result["success"]:
                        logger.info(f"✅ Motor alternativo {alternative_engine} funcionó correctamente")
                    else:
                        logger.warning(f"⚠️ Motor alternativo {alternative_engine} también falló")
                except Exception as alt_e:
                    logger.warning(f"⚠️ Error con motor alternativo: {alt_e}")
            
            # Limpiar archivo temporal
            temp_path.unlink(missing_ok=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error procesando imagen desde bytes: {e}")
            return {"success": False, "message": str(e)}

 