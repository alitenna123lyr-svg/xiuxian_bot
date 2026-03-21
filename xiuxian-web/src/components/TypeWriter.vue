<script setup lang="ts">
/**
 * TypeWriter – 逐字显示文本，修仙剧情核心体验组件
 *
 * Props:
 *  text     - 要显示的完整文本
 *  speed    - 每字毫秒数 (默认 40)
 *  onDone   - 打完回调
 *
 * 点击可跳过打字直接显示全文
 */
const props = withDefaults(defineProps<{
  text: string
  speed?: number
}>(), {
  speed: 40,
})

const emit = defineEmits<{
  done: []
}>()

const displayed = ref('')
const isDone = ref(false)
let timer: ReturnType<typeof setTimeout> | null = null
let charIndex = 0

function tick() {
  if (charIndex >= props.text.length) {
    isDone.value = true
    emit('done')
    return
  }
  displayed.value += props.text[charIndex]
  charIndex++
  timer = setTimeout(tick, props.speed)
}

function skip() {
  if (timer) clearTimeout(timer)
  displayed.value = props.text
  isDone.value = true
  emit('done')
}

function reset() {
  if (timer) clearTimeout(timer)
  displayed.value = ''
  isDone.value = false
  charIndex = 0
  tick()
}

watch(() => props.text, () => {
  reset()
})

onMounted(() => {
  reset()
})

onUnmounted(() => {
  if (timer) clearTimeout(timer)
})
</script>

<template>
  <span class="typewriter" @click="skip">
    <span v-html="displayed.replace(/\n/g, '<br>')"></span>
    <span v-if="!isDone" class="typewriter-cursor"></span>
  </span>
</template>

<style scoped>
.typewriter {
  cursor: pointer;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}
</style>
