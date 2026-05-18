<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as monaco from 'monaco-editor'

const props = defineProps<{
  modelValue: string
  language?: string
  theme?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const host = ref<HTMLDivElement | null>(null)
const isFullscreen = ref(false)
let editor: monaco.editor.IStandaloneCodeEditor | undefined
let subscription: monaco.IDisposable | undefined
let resizeObserver: ResizeObserver | undefined

onMounted(() => {
  if (!host.value) return
  editor = monaco.editor.create(host.value, {
    value: props.modelValue,
    language: props.language || 'python',
    theme: props.theme || 'vs-dark',
    automaticLayout: true,
    minimap: { enabled: false },
    fontSize: 13,
    lineNumbersMinChars: 3,
    scrollBeyondLastLine: false,
    tabSize: 4,
    wordWrap: 'on'
  })
  subscription = editor.onDidChangeModelContent(() => {
    emit('update:modelValue', editor?.getValue() || '')
  })
  resizeObserver = new ResizeObserver(() => editor?.layout())
  resizeObserver.observe(host.value)
})

watch(
  () => props.modelValue,
  (value) => {
    if (editor && value !== editor.getValue()) editor.setValue(value)
  }
)

watch(
  () => props.language,
  (language) => {
    const model = editor?.getModel()
    if (model) monaco.editor.setModelLanguage(model, language || 'python')
  }
)

onBeforeUnmount(() => {
  subscription?.dispose()
  resizeObserver?.disconnect()
  editor?.dispose()
})

async function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  await nextTick()
  editor?.layout()
}
</script>

<template>
  <div :class="['code-editor-shell', { fullscreen: isFullscreen }]">
    <button class="fullscreen-toggle" type="button" @click="toggleFullscreen">
      {{ isFullscreen ? '退出全屏' : '全屏' }}
    </button>
    <div ref="host" class="code-editor"></div>
  </div>
</template>
