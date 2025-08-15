<template>
  <div class="help-section">
    <h4>⌨️ Atajos:</h4>
    <p><strong>Espacio:</strong> Capturar y procesar | <strong>Escape:</strong> Nueva foto</p>
    
    <h4>🆕 Nuevas características v3.0:</h4>
    <p>• OCR.Space API para máxima precisión</p>
    <p>• Procesamiento en servidor optimizado</p>
    <p>• Preprocesamiento avanzado de imágenes</p>
    <p>• Múltiples motores OCR (engine 1, 2, 3)</p>
    <p>• 🎯 Marco de enfoque inteligente para mejor precisión</p>
    <p>• 📐 Controles ajustables del área de captura</p>
  </div>
</template>

<script setup>
</script>

<style scoped>
.help-section {
  background: #f7fafc;
  padding: 15px;
  border-radius: 12px;
  margin-top: 20px;
  font-size: 12px;
  color: #718096;
}

.help-section h4 {
  color: #2d3748;
  margin-bottom: 8px;
}

.help-section h4:not(:first-child) {
  margin-top: 15px;
}

.help-section p {
  margin-bottom: 4px;
}
</style>