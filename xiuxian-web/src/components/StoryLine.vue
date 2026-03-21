<script setup lang="ts">
/**
 * StoryLine – 单条剧情行渲染 (水墨风)
 * 旁白 → 横排竖线分隔
 * 对话 → NPC 名篆 + 气泡
 * 选择 → 金色选项卡
 */
import TypeWriter from './TypeWriter.vue'

const props = defineProps<{
  type: 'narration' | 'dialogue' | 'choice'
  text: string
  speaker?: string
  animate?: boolean
}>()

const emit = defineEmits<{ done: [] }>()

// NPC 名字首字做「篆章」效果
const sealChar = computed(() => props.speaker ? props.speaker.charAt(0) : '')

// NPC 篆章颜色 — 根据名字 hash 分配
const sealColor = computed(() => {
  if (!props.speaker) return 'var(--cinnabar)'
  const colors = ['#c03030', '#b8860b', '#4a8c6f', '#4a6fa5', '#7b5ea7', '#8b6914']
  let h = 0
  for (let i = 0; i < props.speaker.length; i++) h = ((h << 5) - h + props.speaker.charCodeAt(i)) | 0
  return colors[Math.abs(h) % colors.length]
})
</script>

<template>
  <div class="sl" :class="`sl--${type}`">

    <!-- ── 旁白 ── -->
    <template v-if="type === 'narration'">
      <div class="sl__narration">
        <TypeWriter v-if="animate" :text="text" :speed="30" @done="emit('done')" />
        <span v-else v-html="text.replace(/\n/g, '<br>')"></span>
      </div>
    </template>

    <!-- ── 对话（有说话人） ── -->
    <template v-else-if="type === 'dialogue' && speaker">
      <div class="sl__dialogue">
        <div class="sl__seal" :style="{ background: sealColor }">{{ sealChar }}</div>
        <div class="sl__bubble">
          <div class="sl__speaker" :style="{ color: sealColor }">{{ speaker }}</div>
          <div class="sl__text">
            <TypeWriter v-if="animate" :text="text" :speed="35" @done="emit('done')" />
            <span v-else v-html="text.replace(/\n/g, '<br>')"></span>
          </div>
        </div>
      </div>
    </template>

    <!-- ── 对话（无说话人 = 旁白式内心独白） ── -->
    <template v-else-if="type === 'dialogue'">
      <div class="sl__inner">
        <TypeWriter v-if="animate" :text="text" :speed="30" @done="emit('done')" />
        <span v-else v-html="text.replace(/\n/g, '<br>')"></span>
      </div>
    </template>

    <!-- ── 选择 ── -->
    <template v-else-if="type === 'choice'">
      <div class="sl__choice">{{ text }}</div>
    </template>
  </div>
</template>

<style scoped>
.sl { margin-bottom: var(--space-md); animation: fade-in var(--duration-normal) var(--ease-out) both; }

/* ── 旁白 ── */
.sl__narration {
  color: var(--ink-dark); line-height: 1.9;
  padding: var(--space-xs) 0 var(--space-xs) var(--space-md);
  border-left: 2px solid var(--paper-deeper);
}

/* ── 对话 ── */
.sl__dialogue { display: flex; gap: var(--space-sm); align-items: flex-start; }
.sl__seal {
  width: 32px; height: 32px; border-radius: 4px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.85rem; font-weight: 700; color: #f5e6c8;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.15);
}
.sl__bubble {
  flex: 1; background: var(--paper-dark);
  border: 1px solid var(--paper-deeper);
  border-radius: 2px var(--radius-sm) var(--radius-sm) var(--radius-sm);
  padding: var(--space-sm) var(--space-md);
  position: relative;
}
.sl__bubble::before {
  content: ''; position: absolute; left: -6px; top: 8px;
  width: 0; height: 0;
  border-top: 5px solid transparent; border-bottom: 5px solid transparent;
  border-right: 6px solid var(--paper-deeper);
}
.sl__speaker { font-size: 0.7rem; font-weight: 700; margin-bottom: 2px; }
.sl__text { color: var(--ink-dark); line-height: 1.8; font-size: 0.88rem; }

/* ── 内心独白 ── */
.sl__inner {
  color: var(--ink-mid); line-height: 1.8; font-style: italic;
  padding: var(--space-xs) var(--space-md);
}

/* ── 选择 ── */
.sl__choice {
  background: var(--paper-dark); border: 1px solid var(--gold);
  border-radius: var(--radius-sm); padding: var(--space-sm) var(--space-md);
  color: var(--gold); font-weight: 600; font-size: 0.85rem;
  cursor: pointer; transition: background var(--duration-fast);
}
.sl__choice:active { background: rgba(184,134,11,0.1); }
</style>
