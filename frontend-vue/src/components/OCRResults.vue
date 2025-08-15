<template>
  <div v-show="visible">
    <label for="extractedText">Texto Extraído:</label>
    <div class="confidence-bar">
      <div class="confidence-fill" :style="{ width: confidence + '%' }"></div>
    </div>
    <textarea 
      id="extractedText"
      :value="text"
      @input="$emit('update:text', $event.target.value)"
      class="text-area" 
      placeholder="Texto extraído aparecerá aquí..."
    ></textarea>
    
    <div class="results-controls">
      <button class="btn btn-secondary" @click="$emit('copy-text', text)">
        📋 Copiar
      </button>
      <button class="btn btn-secondary" @click="$emit('retake')">
        🔄 Nueva Foto
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: ''
  },
  confidence: {
    type: Number,
    default: 0
  },
  visible: {
    type: Boolean,
    default: false
  }
})

defineEmits(['copy-text', 'retake', 'update:text'])
</script>

<style scoped>
label {
  display: block;
  margin-bottom: 10px;
  font-weight: 600;
  color: #2d3748;
}

.confidence-bar {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
  margin: 10px 0;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #fc8181 0%, #f6e05e 50%, #68d391 100%);
  transition: width 0.3s;
}

.text-area {
  width: 100%;
  min-height: 120px;
  padding: 15px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 16px;
  resize: vertical;
  font-family: inherit;
  margin-bottom: 15px;
}

.text-area:focus {
  outline: none;
  border-color: #667eea;
}

.results-controls {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 10px;
}
</style>