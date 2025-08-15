<template>
  <div class="progress-container">
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: percentage + '%' }"></div>
    </div>
    <div class="progress-text">{{ text }}</div>
  </div>
</template>

<script setup>
defineProps({
  percentage: {
    type: Number,
    default: 0
  },
  text: {
    type: String,
    default: 'Inicializando...'
  }
})
</script>

<style scoped>
.progress-container {
  background: #f7fafc;
  border-radius: 8px;
  padding: 10px;
  margin: 10px 0;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s;
}

.progress-text {
  text-align: center;
  font-size: 14px;
  color: #4a5568;
  margin-top: 5px;
}
</style>