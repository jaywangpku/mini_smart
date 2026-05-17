<script setup lang="ts">
import { Menu, PanelLeftClose } from 'lucide-vue-next'

defineProps<{
  tabs: Array<{ id: string; label: string; icon: unknown }>
  activeTab: string
  collapsed: boolean
}>()

const emit = defineEmits<{
  'update:activeTab': [value: string]
  'update:collapsed': [value: boolean]
}>()
</script>

<template>
  <aside class="side-nav">
    <div class="brand">
      <button class="icon-button" title="收起导航" @click="emit('update:collapsed', !collapsed)">
        <PanelLeftClose v-if="!collapsed" :size="18" />
        <Menu v-else :size="18" />
      </button>
      <div v-if="!collapsed">
        <h1>量化研究台</h1>
      </div>
    </div>
    <nav class="side-tabs">
      <button v-for="tab in tabs" :key="tab.id" :class="{ active: activeTab === tab.id }" @click="emit('update:activeTab', tab.id)">
        <component :is="tab.icon" :size="18" />
        <span v-if="!collapsed">{{ tab.label }}</span>
      </button>
    </nav>
  </aside>
</template>
