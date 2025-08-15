<template>
  <div :class="['status', `status-${type}`]">
    {{ message }}
  </div>
</template>

<script setup>
defineProps({
  message: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'info',
    validator: (value) => ['info', 'success', 'error'].includes(value)
  }
})
</script>

<style scoped>
.status {
  padding: 15px;
  border-radius: 12px;
  margin-bottom: 20px;
  font-weight: 500;
  text-align: center;
}

.status-info {
  background: #bee3f8;
  color: #2c5282;
  border: 2px solid #90cdf4;
}

.status-success {
  background: #c6f6d5;
  color: #22543d;
  border: 2px solid #9ae6b4;
}

.status-error {
  background: #fed7d7;
  color: #742a2a;
  border: 2px solid #fc8181;
}
</style>