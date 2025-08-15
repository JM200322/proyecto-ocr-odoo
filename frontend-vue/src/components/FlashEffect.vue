<template>
  <div ref="flashDiv" class="flash-effect"></div>
</template>

<script setup>
import { ref } from 'vue'

const flashDiv = ref(null)

const trigger = () => {
  if (flashDiv.value) {
    flashDiv.value.style.opacity = '0.8'
    setTimeout(() => {
      if (flashDiv.value) {
        flashDiv.value.style.opacity = '0'
      }
    }, 150)
  }
}

defineExpose({
  trigger
})
</script>

<style scoped>
.flash-effect {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: white;
  opacity: 0;
  pointer-events: none;
  z-index: 9999;
  transition: opacity 0.15s;
}
</style>