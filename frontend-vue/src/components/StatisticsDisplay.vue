<template>
  <div class="stats">
    <div class="stat-card">
      <div class="stat-number">{{ processed }}</div>
      <div class="stat-label">Procesados</div>
    </div>
    <div class="stat-card">
      <div class="stat-number">{{ avgConfidence }}%</div>
      <div class="stat-label">Confianza</div>
    </div>
    <div class="stat-card">
      <div class="stat-number">{{ avgTime }}s</div>
      <div class="stat-label">Tiempo Prom.</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  processed: {
    type: Number,
    default: 0
  },
  avgConfidence: {
    type: Number,
    default: 0
  },
  avgTime: {
    type: Number,
    default: 0
  }
})
</script>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 25px;
}

.stat-card {
  background: #f7fafc;
  padding: 15px;
  border-radius: 12px;
  text-align: center;
  border: 2px solid #e2e8f0;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #2d3748;
}

.stat-label {
  font-size: 12px;
  color: #718096;
  margin-top: 5px;
}

@media (max-width: 480px) {
  .stats {
    grid-template-columns: 1fr;
  }
}
</style>