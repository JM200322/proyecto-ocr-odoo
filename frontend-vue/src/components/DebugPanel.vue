<template>
  <div>
    <div style="margin-top: 20px;">
      <button 
        :class="['btn', active ? 'btn-success' : 'btn-secondary']" 
        @click="$emit('toggle')"
        style="margin-bottom: 10px;"
      >
        {{ active ? '🐛 Debug: ON' : '🐛 Modo Debug' }}
      </button>
    </div>

    <div class="debug-info" v-show="active">
      <div v-for="(log, index) in logs" :key="index">
        {{ log }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  active: {
    type: Boolean,
    default: false
  },
  logs: {
    type: Array,
    default: () => []
  }
})

defineEmits(['toggle'])
</script>

<style scoped>
.debug-info {
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px;
  margin: 10px 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #4a5568;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-line;
}
</style>