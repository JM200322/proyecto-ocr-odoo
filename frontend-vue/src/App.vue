<template>
  <div class="container">
    <AppHeader />
    <StatisticsDisplay 
      :processed="stats.processed"
      :avgConfidence="stats.avgConfidence"
      :avgTime="stats.avgTime"
    />
    <StatusMessage 
      :message="status.message"
      :type="status.type"
      v-if="status.message"
    />
    <DocumentTypeIndicator 
      :documentType="documentType"
      v-show="documentType"
    />
    <ProgressIndicator 
      :percentage="progress.percentage"
      :text="progress.text"
      v-show="progress.visible"
    />
    <CameraComponent
      @capture-complete="handleCaptureComplete"
      @status-change="handleStatusChange"
      @progress-change="handleProgressChange"
    />
    <OCRResults 
      :text="ocrResult.text"
      :confidence="ocrResult.confidence"
      :visible="ocrResult.visible"
      @copy-text="copyToClipboard"
      @retake="retakePhoto"
    />
    <DebugPanel 
      :active="debugMode"
      :logs="debugLogs"
      @toggle="toggleDebug"
    />
    <HelpSection />
    <FlashEffect ref="flashEffect" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { BACKEND_URL } from './config.js'
import AppHeader from './components/AppHeader.vue'
import StatisticsDisplay from './components/StatisticsDisplay.vue'
import StatusMessage from './components/StatusMessage.vue'
import DocumentTypeIndicator from './components/DocumentTypeIndicator.vue'
import ProgressIndicator from './components/ProgressIndicator.vue'
import CameraComponent from './components/CameraComponent.vue'
import OCRResults from './components/OCRResults.vue'
import DebugPanel from './components/DebugPanel.vue'
import HelpSection from './components/HelpSection.vue'
import FlashEffect from './components/FlashEffect.vue'

// Estado reactivo
const stats = reactive({
  processed: 0,
  confidenceSum: 0,
  timeSum: 0,
  avgConfidence: 0,
  avgTime: 0
})

const status = reactive({
  message: '',
  type: 'info'
})

const progress = reactive({
  visible: false,
  percentage: 0,
  text: ''
})

const ocrResult = reactive({
  text: '',
  confidence: 0,
  visible: false
})

const documentType = ref('')
const debugMode = ref(false)
const debugLogs = ref([])
const flashEffect = ref(null)

// Métodos
const handleStatusChange = (message, type) => {
  status.message = message
  status.type = type
  
  if (type === 'success') {
    setTimeout(() => {
      status.message = ''
    }, 5000)
  }
  
  debugLog(`Status [${type}]: ${message}`)
}

const handleProgressChange = (percentage, text) => {
  progress.visible = percentage > 0 && percentage < 100
  progress.percentage = percentage
  progress.text = text
}

const handleCaptureComplete = (result) => {
  ocrResult.text = result.text
  ocrResult.confidence = result.confidence
  ocrResult.visible = true
  
  updateStats(result.confidence, result.processingTime)
  
  // Flash effect
  if (flashEffect.value) {
    flashEffect.value.trigger()
  }
}

const updateStats = (confidence, time) => {
  stats.processed++
  stats.confidenceSum += confidence
  stats.timeSum += time
  stats.avgConfidence = Math.round(stats.confidenceSum / stats.processed)
  stats.avgTime = Number((stats.timeSum / stats.processed).toFixed(1))
}

const copyToClipboard = async (text) => {
  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text)
    } else {
      // Fallback para navegadores antiguos
      const textArea = document.createElement('textarea')
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
    }
    handleStatusChange('📋 Texto copiado al portapapeles', 'success')
  } catch (error) {
    handleStatusChange('Error al copiar texto', 'error')
  }
}

const retakePhoto = () => {
  ocrResult.visible = false
  ocrResult.text = ''
  ocrResult.confidence = 0
  documentType.value = ''
  status.message = ''
}

const toggleDebug = () => {
  debugMode.value = !debugMode.value
  if (debugMode.value) {
    handleStatusChange('🐛 Modo debug activado - Sistema OCR v3.0', 'info')
  }
}

const debugLog = (message) => {
  console.log('[DEBUG v3.0]', message)
  
  if (debugMode.value) {
    const timestamp = new Date().toLocaleTimeString()
    debugLogs.value.push(`[${timestamp}] ${message}`)
    
    // Mantener solo los últimos 50 logs
    if (debugLogs.value.length > 50) {
      debugLogs.value = debugLogs.value.slice(-50)
    }
  }
}

const checkBackendConnection = async () => {
  try {
    console.log('🔍 Probando conexión con:', `${BACKEND_URL}/api/health`)
    
    const response = await fetch(`${BACKEND_URL}/api/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    console.log('📡 Respuesta del servidor:', response.status, response.statusText)
    
    const data = await response.json()
    console.log('📊 Datos de respuesta:', data)
    
    if (data.success) {
      console.log('✅ Backend OCR.Space conectado correctamente')
      return true
    } else {
      console.error('❌ Backend no disponible:', data)
      return false
    }
  } catch (error) {
    console.error('❌ Error conectando con backend:', error)
    console.error('🔗 URL intentada:', `${BACKEND_URL}/api/health`)
    console.error('🌐 Hostname actual:', window.location.hostname)
    console.error('📱 User Agent:', navigator.userAgent)
    return false
  }
}

// Inicialización
onMounted(async () => {
  console.log('🔗 Backend URL configurada:', BACKEND_URL)
  
  const connected = await checkBackendConnection()
  if (!connected) {
    handleStatusChange('❌ Error: No se pudo conectar con el servidor OCR. Verifica que el backend esté ejecutándose.', 'error')
  } else {
    // Mostrar mensaje de bienvenida
    setTimeout(() => {
      handleStatusChange('🚀 Sistema OCR v3.0 listo con OCR.Space API. Inicia la cámara para comenzar.', 'info')
      debugLog('Sistema OCR v3.0 completamente inicializado')
      
      // Mostrar tip aleatorio
      const tips = [
        '💡 Tip: El sistema usa OCR.Space API para máxima precisión',
        '💡 Tip: Usa Ctrl+D para activar el modo debug avanzado', 
        '💡 Tip: El preprocesamiento mejora automáticamente la imagen'
      ]
      
      setTimeout(() => {
        const randomTip = tips[Math.floor(Math.random() * tips.length)]
        handleStatusChange(randomTip, 'info')
      }, 3000)
    }, 2000)
  }
  
  debugLog('=== SISTEMA OCR v3.0 INICIALIZADO ===')
  debugLog('Características habilitadas:')
  debugLog('- OCR.Space API para máxima precisión')
  debugLog('- Procesamiento en servidor optimizado')
  debugLog('- Preprocesamiento avanzado de imagen')
  debugLog('- Múltiples motores OCR (engine 1, 2, 3)')
  debugLog('- Post-procesamiento inteligente')
  debugLog('- Análisis de calidad de imagen')
  debugLog('- Métricas de rendimiento')
  debugLog('=====================================')
})

// Atajos de teclado globales
onMounted(() => {
  const handleKeydown = (e) => {
    if (e.target.matches('input, textarea')) return
    
    if (e.ctrlKey && e.key === 'd') {
      e.preventDefault()
      toggleDebug()
    }
    
    if (e.ctrlKey && e.key === 'c' && ocrResult.visible) {
      copyToClipboard(ocrResult.text)
    }
  }
  
  document.addEventListener('keydown', handleKeydown)
  
  // Cleanup
  return () => {
    document.removeEventListener('keydown', handleKeydown)
  }
})
</script>