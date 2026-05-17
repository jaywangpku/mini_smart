<script setup lang="ts">
defineProps<{
  message: string
  error: string
}>()
</script>

<template>
  <div v-if="message || error" :class="['toast', error ? 'error' : 'notice']">
    {{ error || message }}
  </div>
</template>
