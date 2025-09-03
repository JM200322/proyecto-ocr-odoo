<template>
  <div>
    <!-- Cámara/Canvas -->
    <div class="camera-container">
      <video 
        ref="video" 
        autoplay 
        muted 
        playsinline 
        v-show="showVideo"
      ></video>
      <canvas 
        ref="canvas" 
        v-show="showCanvas"
      ></canvas>
      <div class="camera-overlay" v-show="showVideo">
        <div 
          class="scan-frame" 
          :style="frameStyle"
        ></div>
      </div>
    </div>

    <!-- Preview de imagen capturada -->
    <div class="image-preview" v-show="previewImage">
      <img :src="previewImage" alt="Imagen capturada">
    </div>

    <!-- Controles de Cámara -->
    <div class="camera-controls">
      <button 
        class="btn btn-primary" 
        @click="toggleCamera"
      >
        {{ cameraButtonText }}
      </button>
    </div>

    <!-- Modo de OCR -->
    <div class="ocr-mode-controls">
      <label class="mode-toggle">
        <input 
          type="checkbox" 
          v-model="digitsOnly"
          class="mode-checkbox"
        >
        <span class="mode-label">📊 Solo dígitos (medidores)</span>
        <div class="mode-description">Optimizado para leer números en medidores, displays y contadores</div>
      </label>
    </div>


    <button 
      class="btn btn-success" 
      @click="captureAndProcess" 
      :disabled="!stream || isProcessing"
    >
      📸 Capturar y Procesar (Espacio)
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { BACKEND_URL } from '../config.js'

const emit = defineEmits(['capture-complete', 'status-change', 'progress-change'])

// Referencias del DOM
const video = ref(null)
const canvas = ref(null)

// Estado reactivo
const stream = ref(null)
const currentCamera = ref('environment')
const isProcessing = ref(false)
const showVideo = ref(false)
const showCanvas = ref(false)
const previewImage = ref('')
// Marco fijo centrado (80% ancho, 60% alto)
const frameWidth = 80
const frameHeight = 60
const digitsOnly = ref(false)

// Computed
const cameraButtonText = computed(() => {
  return stream.value ? '⏹️ Detener Cámara' : '📷 Iniciar Cámara'
})

const frameStyle = computed(() => ({
  width: frameWidth + '%',
  height: frameHeight + '%'
}))

// Métodos
const toggleCamera = async () => {
  if (stream.value) {
    stopCamera()
  } else {
    try {
      await startCamera()
    } catch (error) {
      emit('status-change', `Error al acceder a la cámara: ${error.message}`, 'error')
    }
  }
}

const startCamera = async () => {
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('Tu navegador no soporta acceso a la cámara')
    }

    const constraints = {
      video: {
        facingMode: currentCamera.value,
        width: { ideal: 1920, min: 1280 },
        height: { ideal: 1080, min: 720 },
        frameRate: { ideal: 30 }
      }
    }

    stream.value = await navigator.mediaDevices.getUserMedia(constraints)
    video.value.srcObject = stream.value
    
    showVideo.value = true
    showCanvas.value = false
    previewImage.value = ''
    
    emit('status-change', '📷 Cámara activa. Sistema OCR v3.0 preparado para análisis con OCR.Space.', 'info')
    console.log(`Cámara iniciada: ${video.value.videoWidth}x${video.value.videoHeight}`)
    
  } catch (error) {
    let errorMessage = 'Error al acceder a la cámara'
    
    if (error.name === 'NotAllowedError') {
      errorMessage = 'Permiso denegado. Permite el acceso a la cámara.'
    } else if (error.name === 'NotFoundError') {
      errorMessage = 'No se encontró cámara en el dispositivo.'
    } else if (error.name === 'NotReadableError') {
      errorMessage = 'La cámara está siendo usada por otra aplicación.'
    }
    
    throw new Error(errorMessage)
  }
}

const stopCamera = () => {
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
    stream.value = null
    video.value.srcObject = null
    
    showVideo.value = false
    showCanvas.value = false
    previewImage.value = ''
    
    emit('status-change', '', 'info')
  }
}



const captureAndProcess = async () => {
  if (!stream.value || isProcessing.value) return

  // Verificar conexión con backend
  try {
    const response = await fetch(`${BACKEND_URL}/api/health`)
    const data = await response.json()
    if (!data.success) {
      emit('status-change', '❌ Servidor OCR no disponible. Verifica que el backend esté ejecutándose.', 'error')
      return
    }
  } catch (error) {
    emit('status-change', '❌ No se pudo conectar con el servidor OCR. Verifica la conexión.', 'error')
    return
  }

  isProcessing.value = true

  try {
    if (video.value.videoWidth === 0 || video.value.videoHeight === 0) {
      throw new Error('El video no está listo. Espera un momento.')
    }

    console.log(`=== INICIANDO CAPTURA Y PROCESAMIENTO v3.0 ===`)
    console.log(`Capturando imagen: ${video.value.videoWidth}x${video.value.videoHeight}`)

    // Capturar solo el área del marco verde
    // Calcular coordenadas directamente sobre la resolución del video
    const videoWidth = video.value.videoWidth
    const videoHeight = video.value.videoHeight
    
    // Calcular el marco en la resolución real del video
    const sourceWidth = (frameWidth / 100) * videoWidth
    const sourceHeight = (frameHeight / 100) * videoHeight
    const sourceX = (videoWidth - sourceWidth) / 2
    const sourceY = (videoHeight - sourceHeight) / 2
    
    // Configurar canvas para la resolución del marco recortado
    const ctx = canvas.value.getContext('2d')
    canvas.value.width = Math.round(sourceWidth)
    canvas.value.height = Math.round(sourceHeight)
    
    // Limpiar canvas
    ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
    
    ctx.imageSmoothingEnabled = true
    ctx.imageSmoothingQuality = 'high'
    
    // Capturar SOLO el área del marco (recortar)
    ctx.drawImage(
      video.value,
      Math.round(sourceX), Math.round(sourceY), Math.round(sourceWidth), Math.round(sourceHeight),  // Área fuente (solo el marco)
      0, 0, Math.round(sourceWidth), Math.round(sourceHeight)                                       // Área destino (canvas completo)
    )
    
    console.log(`📐 Marco de enfoque: ${Math.round(sourceWidth)}x${Math.round(sourceHeight)}px`)
    console.log(`📍 Posición: (${Math.round(sourceX)}, ${Math.round(sourceY)})`)

    // Mostrar imagen capturada
    showVideo.value = false
    showCanvas.value = true
    
    // Mostrar preview
    previewImage.value = canvas.value.toDataURL('image/jpeg', 0.95)

    // Procesar con sistema avanzado
    await processOCRWithAdvancedSystem()

  } catch (error) {
    console.error('Error en captura:', error)
    emit('status-change', `Error: ${error.message}`, 'error')
  } finally {
    isProcessing.value = false
  }
}

const processOCRWithAdvancedSystem = async () => {
  const startTime = performance.now()
  
  emit('progress-change', 0, 'Iniciando procesamiento con OCR.Space...')
  
  try {
    // PASO 1: Preparar imagen para envío
    emit('progress-change', 10, 'Preparando imagen...')
    const imageData = canvas.value.toDataURL('image/jpeg', 0.9)
    
    // PASO 2: Enviar al backend
    emit('progress-change', 30, 'Enviando al servidor OCR.Space...')
    const response = await fetch(`${BACKEND_URL}/api/process-ocr`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        image_data: imageData,
        brightness: 0,
        contrast: 100,
        sharpness: 0,
        digits_only: digitsOnly.value
      })
    })
    
    if (!response.ok) {
      throw new Error(`Error del servidor: ${response.status}`)
    }
    
    const result = await response.json()
    
    if (!result.success) {
      throw new Error(result.message || 'Error en el procesamiento OCR')
    }
    
    emit('progress-change', 90, 'Procesando resultados...')
    
    // PASO 3: Mostrar resultados
    const processedText = result.text || ''
    const confidence = result.confidence || 0
    const processingTime = result.processing_time || 0
    
    emit('progress-change', 100, 'Completado')
    
    // Emitir resultado
    emit('capture-complete', {
      text: processedText,
      confidence: confidence,
      processingTime: processingTime,
      details: result.details
    })

    // Mensaje de estado mejorado
    let statusMessage = `✅ Texto extraído: ${processedText.length} caracteres`
    statusMessage += ` (${Math.round(confidence)}% confianza, ${processingTime.toFixed(1)}s)`
    
    if (confidence >= 90) {
      statusMessage = '🎯 ' + statusMessage + ' - Excelente precisión!'
    } else if (confidence >= 70) {
      statusMessage = '👍 ' + statusMessage + ' - Buena precisión'
    } else {
      statusMessage = '⚠️ ' + statusMessage + ' - Considera mejorar la imagen'
    }
    
    emit('status-change', statusMessage, 'success')
    console.log(`=== PROCESAMIENTO COMPLETADO EXITOSAMENTE ===`)
    console.log(`Detalles del procesamiento: ${JSON.stringify(result.details)}`)

  } catch (error) {
    emit('progress-change', 0, '')
    console.error('Error en OCR con backend:', error)
    emit('status-change', `❌ Error en procesamiento: ${error.message}`, 'error')
    console.log(`Error completo: ${error.toString()}`)
  }
}

// Atajos de teclado
const handleKeydown = (e) => {
  if (e.target.matches('input, textarea')) return
  
  if (e.code === 'Space') {
    e.preventDefault()
    if (!isProcessing.value && stream.value) {
      captureAndProcess()
    }
  }
  
  if (e.key === 'Escape') {
    e.preventDefault()
    if (showCanvas.value) {
      showVideo.value = true
      showCanvas.value = false
      previewImage.value = ''
    }
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
  }
})
</script>

<style scoped>
.camera-container {
  position: relative;
  width: 100%;
  height: 300px;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 20px;
  background: #2d3748;
}

video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

canvas {
  width: 100%;
  height: auto;
  max-height: 300px;
  object-fit: contain;
  background: #f7fafc;
  border-radius: 12px;
  border: 2px solid #38a169;
}

.camera-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.scan-frame {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border: 3px solid #38a169;
  border-radius: 12px;
  background: rgba(56, 161, 105, 0.1);
}

.camera-controls {
  margin-bottom: 20px;
}

.ocr-mode-controls {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 12px;
  border: 2px solid #e9ecef;
}

.mode-toggle {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.mode-checkbox {
  margin: 0;
  transform: scale(1.2);
}

.mode-label {
  font-weight: 600;
  color: #2d3748;
  font-size: 16px;
}

.mode-description {
  font-size: 13px;
  color: #718096;
  margin-top: 4px;
  margin-left: 20px;
}


.image-preview {
  margin: 15px 0;
}

.image-preview img {
  width: 100%;
  max-height: 200px;
  object-fit: contain;
  border-radius: 8px;
  border: 2px solid #e2e8f0;
}

@media (max-width: 480px) {
  .camera-controls {
    grid-template-columns: 1fr;
  }
}
</style>