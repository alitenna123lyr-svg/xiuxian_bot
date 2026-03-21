<script setup lang="ts">
/** 乾坤袋 – 物品列表 + 装备管理 */
import { usePlayerStore } from '@/stores/player'
import { getItems, useItem, equipItem } from '@/api/client'

const player = usePlayerStore()
const items = ref<any[]>([])
const loading = ref(true)
const msg = ref('')

onMounted(async () => {
  if (!player.userId) return
  try {
    const r = await getItems(player.userId)
    items.value = r.items || []
  } catch { items.value = [] }
  loading.value = false
})

async function onUse(item: any) {
  msg.value = ''
  try {
    const r = await useItem(player.userId, item.instance_id)
    msg.value = r.message || '使用成功'
    await player.init()
    // Refresh items
    const ir = await getItems(player.userId)
    items.value = ir.items || []
  } catch (e: any) { msg.value = e.body?.message || '使用失败' }
}

const RARITY_COLORS: Record<string, string> = {
  common: 'var(--ink-mid)',
  uncommon: 'var(--jade)',
  rare: 'var(--azure)',
  epic: 'var(--purple-qi)',
  legendary: 'var(--gold)',
}

function rarityColor(r: string) { return RARITY_COLORS[r] || 'var(--ink-mid)' }
</script>

<template>
  <div class="bag">
    <h2 class="bag__title">🎒 乾坤袋</h2>

    <div v-if="msg" class="bag__msg card fade-in" @click="msg=''">{{ msg }}</div>

    <div v-if="loading" style="display:flex;justify-content:center;padding:60px 0"><div class="loading-spinner"></div></div>

    <div v-else-if="items.length === 0" class="bag__empty">
      <div style="font-size:2rem;margin-bottom:var(--space-sm)">🌀</div>
      <p>乾坤袋空空如也</p>
      <p class="text-dim" style="font-size:0.8rem">去狩猎或签到获取物品</p>
    </div>

    <div v-else class="bag__grid">
      <div
        v-for="item in items" :key="item.instance_id"
        class="bag__item card"
        @click="onUse(item)"
      >
        <div class="bag__item-head">
          <span class="bag__item-name" :style="{ color: rarityColor(item.rarity) }">
            {{ item.name || item.item_id }}
          </span>
          <span v-if="item.quantity > 1" class="bag__item-qty">x{{ item.quantity }}</span>
        </div>
        <p v-if="item.desc" class="bag__item-desc">{{ item.desc }}</p>
        <span v-if="item.equipped" class="bag__item-badge">已装备</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bag { padding: var(--space-lg); padding-bottom: 80px; }
.bag__title { font-size: 1.1rem; margin-bottom: var(--space-md); }
.bag__msg { margin-bottom: var(--space-md); font-size: 0.85rem; cursor: pointer; text-align: center; }
.bag__empty { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 50vh; color: var(--ink-light); }
.bag__grid { display: flex; flex-direction: column; gap: var(--space-sm); }
.bag__item { padding: var(--space-md); cursor: pointer; transition: background var(--duration-fast); position: relative; }
.bag__item:active { background: var(--paper-dark); }
.bag__item-head { display: flex; justify-content: space-between; align-items: baseline; }
.bag__item-name { font-weight: 600; font-size: 0.88rem; }
.bag__item-qty { font-size: 0.75rem; color: var(--ink-light); font-family: var(--font-mono); }
.bag__item-desc { font-size: 0.75rem; color: var(--ink-light); margin-top: 2px; }
.bag__item-badge {
  position: absolute; top: var(--space-sm); right: var(--space-sm);
  font-size: 0.6rem; padding: 1px 6px; border-radius: 2px;
  background: var(--gold); color: #fff;
}
</style>
