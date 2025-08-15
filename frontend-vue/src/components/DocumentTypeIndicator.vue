<template>
  <div class="document-type-indicator">
    📄 Tipo de documento: <span>{{ documentType }}</span>
  </div>
</template>

<script setup>
defineProps({
  documentType: {
    type: String,
    default: 'Analizando...'
  }
})
</script>

<style scoped>
.document-type-indicator {
  background: #e6fffa;
  border: 2px solid #38b2ac;
  color: #234e52;
  padding: 10px;
  border-radius: 8px;
  margin: 10px 0;
  text-align: center;
  font-weight: 600;
}

.document-type-indicator span {
  color: #38b2ac;
  font-weight: bold;
}
</style>