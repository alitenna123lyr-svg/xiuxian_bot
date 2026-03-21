<script setup lang="ts">
/** 更多 – 功能入口面板 */
import { usePlayerStore } from '@/stores/player'

const player = usePlayerStore()
const router = useRouter()
</script>

<template>
  <div class="more">
    <h2 class="more__title">☯ 修仙百务</h2>

    <!-- 功能入口 -->
    <div class="more__grid">
      <button class="more__entry card" @click="router.push('/map')">
        <span class="more__entry-icon">🗺️</span>
        <span>大地图</span>
      </button>
      <button class="more__entry card" @click="router.push('/story')">
        <span class="more__entry-icon">📜</span>
        <span>仙卷剧情</span>
      </button>
      <button class="more__entry card" @click="router.push('/bag')">
        <span class="more__entry-icon">🎒</span>
        <span>乾坤袋</span>
      </button>
      <button class="more__entry card" @click="router.push('/cultivate')">
        <span class="more__entry-icon">🧘</span>
        <span>闭关修炼</span>
      </button>
    </div>

    <!-- 信息 -->
    <div class="card more__section" style="margin-top:var(--space-md)">
      <h3 style="font-size:0.85rem">关于</h3>
      <p class="text-dim" style="font-size:0.75rem;margin-top:4px">修仙之路 · 水墨修仙 MiniApp</p>
    </div>
  </div>
</template>

<style scoped>
.more { padding: var(--space-lg); padding-bottom: 80px; }
.more__title { font-size: 1.1rem; margin-bottom: var(--space-md); }
.more__section { margin-bottom: var(--space-md); }
.more__section h3 { font-size: 0.9rem; }

.more__grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-sm); }
.more__entry {
  display: flex; flex-direction: column; align-items: center; gap: var(--space-xs);
  padding: var(--space-lg) var(--space-md); cursor: pointer;
  font-size: 0.85rem; font-weight: 600; color: var(--ink-dark);
  transition: background var(--duration-fast);
  -webkit-tap-highlight-color: transparent;
}
.more__entry:active { background: var(--paper-dark); }
.more__entry-icon { font-size: 1.5rem; }
</style>
