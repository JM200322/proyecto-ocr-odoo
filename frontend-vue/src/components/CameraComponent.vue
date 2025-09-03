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
        v-show="showCanvas && !showCropEditor"
      ></canvas>
      <div class="camera-overlay" v-show="showVideo">
        <div 
          class="scan-frame" 
          :style="frameStyle"
        ></div>
      </div>
    </div>

    <!-- Editor de Recorte -->
    <div class="crop-editor" v-show="showCropEditor" style="background: yellow; padding: 20px; margin: 20px; border: 5px solid red;">
      <h2 style="color: red; font-size: 24px;">EDITOR DE RECORTE ACTIVO</h2>
      <p>showCropEditor: {{ showCropEditor }}</p>
      <div class="crop-container">
        <canvas 
          ref="cropCanvas"
          @mousedown="startCrop"
          @mousemove="updateCrop"
          @mouseup="endCrop"
          @touchstart="startCrop"
          @touchmove="updateCrop"
          @touchend="endCrop"
          style="border: 3px solid blue;"
        ></canvas>
        <div class="crop-overlay" v-if="cropArea.active">
          <div 
            class="crop-selection"
            :style="cropSelectionStyle"
          ></div>
        </div>
      </div>
      <div class="crop-controls">
        <button class="btn btn-success" @click="applyCrop" :disabled="!cropArea.active">
          ✂️ Recortar y Procesar
        </button>
        <button class="btn btn-secondary" @click="resetCrop">
          🔄 Reiniciar
        </button>
        <button class="btn btn-warning" @click="cancelCrop">
          ❌ Cancelar
        </button>
        <button class="btn btn-info" @click="showCropEditor = !showCropEditor">
          🔧 Toggle Editor (TEST)
        </button>
      </div>
    </div>

    <!-- Preview de imagen capturada -->
    <div class="image-preview" v-show="previewImage && !showCropEditor">
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
      @click="captureImage" 
      :disabled="!stream || isProcessing"
    >
      📸 Capturar Imagen (Espacio)
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
const cropCanvas = ref(null)

// Estado reactivo
const stream = ref(null)
const currentCamera = ref('environment')
const isProcessing = ref(false)
const showVideo = ref(false)
const showCanvas = ref(false)
const showCropEditor = ref(false)
const previewImage = ref('')
const originalImageData = ref('')
// Marco fijo centrado (80% ancho, 60% alto)
const frameWidth = 80
const frameHeight = 60
const digitsOnly = ref(false)

// Estado del editor de recorte
const cropArea = ref({
  active: false,
  startX: 0,
  startY: 0,
  endX: 0,
  endY: 0,
  isDragging: false
})

// Computed
const cameraButtonText = computed(() => {
  return stream.value ? '⏹️ Detener Cámara' : '📷 Iniciar Cámara'
})

const frameStyle = computed(() => ({
  width: frameWidth + '%',
  height: frameHeight + '%'
}))

const cropSelectionStyle = computed(() => {
  if (!cropArea.value.active) return {}
  
  const rect = cropCanvas.value?.getBoundingClientRect()
  if (!rect) return {}
  
  const left = Math.min(cropArea.value.startX, cropArea.value.endX)
  const top = Math.min(cropArea.value.startY, cropArea.value.endY)
  const width = Math.abs(cropArea.value.endX - cropArea.value.startX)
  const height = Math.abs(cropArea.value.endY - cropArea.value.startY)
  
  return {
    left: left + 'px',
    top: top + 'px',
    width: width + 'px',
    height: height + 'px'
  }
})

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



const captureImage = async () => {
  emit('status-change', '🔍 DEBUG: Iniciando captura...', 'info')
  
  if (!stream.value || isProcessing.value) {
    emit('status-change', '❌ DEBUG: No hay stream o está procesando', 'error')
    return
  }

  try {
    if (video.value.videoWidth === 0 || video.value.videoHeight === 0) {
      throw new Error('El video no está listo. Espera un momento.')
    }

    emit('status-change', `📸 DEBUG: Capturando video ${video.value.videoWidth}x${video.value.videoHeight}`, 'info')

    // Capturar imagen completa del video
    const ctx = canvas.value.getContext('2d')
    canvas.value.width = video.value.videoWidth
    canvas.value.height = video.value.videoHeight
    
    ctx.drawImage(video.value, 0, 0)
    
    // Guardar imagen original para el editor de recorte
    originalImageData.value = canvas.value.toDataURL('image/jpeg', 0.95)
    emit('status-change', `💾 DEBUG: Imagen guardada (${Math.round(originalImageData.value.length/1024)}KB)`, 'info')
    
    // Mostrar editor de recorte
    showVideo.value = false
    showCanvas.value = false
    showCropEditor.value = true
    
    emit('status-change', `🔄 DEBUG: Cambiando a editor. showCropEditor=${showCropEditor.value}`, 'info')
    
    // Configurar canvas del editor con la imagen capturada
    setTimeout(() => {
      setupCropEditor()
    }, 100)
    
    setTimeout(() => {
      emit('status-change', '✂️ Selecciona el área a procesar arrastrando sobre la imagen', 'info')
    }, 500)

  } catch (error) {
    console.error('Error en captura:', error)
    emit('status-change', `Error: ${error.message}`, 'error')
  }
}

const setupCropEditor = () => {
  if (!cropCanvas.value || !originalImageData.value) {
    emit('status-change', '❌ DEBUG: Falta cropCanvas o imagen original', 'error')
    return
  }
  
  emit('status-change', '🖼️ DEBUG: Configurando editor de recorte...', 'info')
  
  const img = new Image()
  img.onload = () => {
    emit('status-change', `🎯 DEBUG: Imagen cargada ${img.width}x${img.height}`, 'success')
    
    const ctx = cropCanvas.value.getContext('2d')
    
    // Calcular tamaño para ajustar al contenedor manteniendo aspecto
    const maxWidth = 400
    const maxHeight = 300
    
    let canvasWidth = img.width
    let canvasHeight = img.height
    
    if (canvasWidth > maxWidth) {
      canvasHeight = (canvasHeight * maxWidth) / canvasWidth
      canvasWidth = maxWidth
    }
    
    if (canvasHeight > maxHeight) {
      canvasWidth = (canvasWidth * maxHeight) / canvasHeight
      canvasHeight = maxHeight
    }
    
    cropCanvas.value.width = canvasWidth
    cropCanvas.value.height = canvasHeight
    
    ctx.drawImage(img, 0, 0, canvasWidth, canvasHeight)
    
    // Resetear área de recorte
    cropArea.value.active = false
    
    emit('status-change', `✅ DEBUG: Editor listo ${canvasWidth}x${canvasHeight}`, 'success')
  }
  
  img.onerror = () => {
    emit('status-change', '❌ DEBUG: Error cargando imagen', 'error')
  }
  
  img.src = originalImageData.value
}

// Funciones del editor de recorte
const getEventCoordinates = (e) => {
  const rect = cropCanvas.value.getBoundingClientRect()
  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY
  
  return {
    x: clientX - rect.left,
    y: clientY - rect.top
  }
}

const startCrop = (e) => {
  e.preventDefault()
  const coords = getEventCoordinates(e)
  
  cropArea.value = {
    active: true,
    startX: coords.x,
    startY: coords.y,
    endX: coords.x,
    endY: coords.y,
    isDragging: true
  }
}

const updateCrop = (e) => {
  if (!cropArea.value.isDragging) return
  e.preventDefault()
  
  const coords = getEventCoordinates(e)
  cropArea.value.endX = coords.x
  cropArea.value.endY = coords.y
}

const endCrop = (e) => {
  e.preventDefault()
  cropArea.value.isDragging = false
  
  // Validar que el área tenga un tamaño mínimo
  const width = Math.abs(cropArea.value.endX - cropArea.value.startX)
  const height = Math.abs(cropArea.value.endY - cropArea.value.startY)
  
  if (width < 10 || height < 10) {
    cropArea.value.active = false
    emit('status-change', '⚠️ Área muy pequeña. Selecciona un área más grande.', 'warning')
  } else {
    emit('status-change', '✅ Área seleccionada. Haz clic en "Recortar y Procesar".', 'success')
  }
}

const applyCrop = async () => {
  if (!cropArea.value.active || !cropCanvas.value) return
  
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
    // Calcular coordenadas de recorte en la imagen original
    const canvasRect = cropCanvas.value.getBoundingClientRect()
    const scaleX = canvas.value.width / cropCanvas.value.width
    const scaleY = canvas.value.height / cropCanvas.value.height
    
    const left = Math.min(cropArea.value.startX, cropArea.value.endX) * scaleX
    const top = Math.min(cropArea.value.startY, cropArea.value.endY) * scaleY
    const width = Math.abs(cropArea.value.endX - cropArea.value.startX) * scaleX
    const height = Math.abs(cropArea.value.endY - cropArea.value.startY) * scaleY
    
    // Crear canvas con área recortada
    const croppedCanvas = document.createElement('canvas')
    const croppedCtx = croppedCanvas.getContext('2d')
    croppedCanvas.width = width
    croppedCanvas.height = height
    
    // Extraer área recortada de la imagen original
    const originalCtx = canvas.value.getContext('2d')
    const imageData = originalCtx.getImageData(left, top, width, height)
    croppedCtx.putImageData(imageData, 0, 0)
    
    // Actualizar canvas principal con la imagen recortada
    canvas.value.width = width
    canvas.value.height = height
    const ctx = canvas.value.getContext('2d')
    ctx.putImageData(imageData, 0, 0)
    
    // Actualizar preview
    previewImage.value = canvas.value.toDataURL('image/jpeg', 0.95)
    
    console.log(`✂️ Imagen recortada: ${Math.round(width)}x${Math.round(height)}px`)
    
    // Ocultar editor y mostrar resultado
    showCropEditor.value = false
    showCanvas.value = true
    
    // Procesar con OCR
    await processOCRWithAdvancedSystem()
    
  } catch (error) {
    console.error('Error en recorte:', error)
    emit('status-change', `Error: ${error.message}`, 'error')
  } finally {
    isProcessing.value = false
  }
}

const resetCrop = () => {
  cropArea.value.active = false
  setupCropEditor()
  emit('status-change', '✂️ Selecciona el área a procesar arrastrando sobre la imagen', 'info')
}

const cancelCrop = () => {
  showCropEditor.value = false
  showVideo.value = true
  cropArea.value.active = false
  emit('status-change', '📷 Cámara activa. Toma otra foto si es necesario.', 'info')
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
      captureImage()
    }
  }
  
  if (e.key === 'Escape') {
    e.preventDefault()
    if (showCropEditor.value) {
      cancelCrop()
    } else if (showCanvas.value) {
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

/* Editor de Recorte */
.crop-editor {
  margin-bottom: 20px;
}

.crop-container {
  position: relative;
  display: flex;
  justify-content: center;
  margin-bottom: 15px;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 10px;
  border: 2px solid #e9ecef;
}

.crop-container canvas {
  cursor: crosshair;
  border: 2px solid #4a5568;
  border-radius: 8px;
  background: white;
}

.crop-overlay {
  position: absolute;
  top: 10px;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  display: flex;
  justify-content: center;
}

.crop-selection {
  position: absolute;
  border: 2px dashed #38a169;
  background: rgba(56, 161, 105, 0.2);
  border-radius: 4px;
  pointer-events: none;
}

.crop-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.crop-controls .btn {
  min-width: 120px;
  padding: 10px 15px;
  font-weight: 600;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.crop-controls .btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.crop-controls .btn-success {
  background: #38a169;
  color: white;
}

.crop-controls .btn-success:hover:not(:disabled) {
  background: #2f855a;
}

.crop-controls .btn-secondary {
  background: #718096;
  color: white;
}

.crop-controls .btn-secondary:hover {
  background: #4a5568;
}

.crop-controls .btn-warning {
  background: #ed8936;
  color: white;
}

.crop-controls .btn-warning:hover {
  background: #dd6b20;
}

@media (max-width: 480px) {
  .camera-controls {
    grid-template-columns: 1fr;
  }
  
  .crop-controls {
    flex-direction: column;
  }
  
  .crop-controls .btn {
    min-width: auto;
    width: 100%;
  }
}
</style>