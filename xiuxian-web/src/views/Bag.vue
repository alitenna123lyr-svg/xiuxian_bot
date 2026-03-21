<script setup lang="ts">
import IcBag from '~icons/mdi/bag-personal'
import IcEquip from '~icons/mdi/sword'
import IcUse from '~icons/mdi/hand-pointing-right'
import { usePlayerStore } from '@/stores/player'
import { getItems, useItem, equipItem } from '@/api/client'

const player = usePlayerStore()
const items = ref<any[]>([])
const loading = ref(true)
const msg = ref('')
const acting = ref(false)

onMounted(async () => {
  if (!player.loaded && player.userId) await player.init()
  await load()
})

async function load() {
  if (!player.userId) return
  loading.value = true
  try {
    const r = await getItems(player.userId)
    items.value = r.items || []
  } catch { items.value = [] }
  loading.value = false
}

async function onUse(item: any) {
  if (acting.value) return
  acting.value = true; msg.value = ''
  try {
    const r = await useItem(player.userId, item.instance_id)
    msg.value = r.message || '使用成功'
    await player.init(true); await load()
  } catch (e: any) { msg.value = e?.body?.message || '使用失败' }
  finally { acting.value = false }
}

async function onEquip(item: any) {
  if (acting.value) return
  acting.value = true; msg.value = ''
  try {
    const slot = item.slot || item.type || 'weapon'
    const r = await equipItem(player.userId, item.instance_id, slot)
    msg.value = r.message || '装备成功'
    await player.init(true); await load()
  } catch (e: any) { msg.value = e?.body?.message || '装备失败' }
  finally { acting.value = false }
}

const RARITY: Record<string, string> = {
  common: 'var(--ink-mid)', uncommon: 'var(--jade)', rare: 'var(--azure)', epic: 'var(--purple-qi)', legendary: 'var(--gold)',
}
</script>

<template>
  <div class="bag-page">
    <h2 class="page-title"><IcBag class="icon" /> 乾坤袋</h2>
    <p v-if="msg" class="msg card fade-in" @click="msg=''">{{ msg }}</p>

    <div v-if="loading" class="page-loading"><div class="loading-spinner"></div></div>

    <div v-else-if="!items.length" class="page-empty">
      <p>乾坤袋空空如也</p>
      <p class="text-dim" style="font-size:.78rem">去狩猎或商店获取物品</p>
    </div>

    <div v-else class="item-list">
      <div v-for="item in items" :key="item.instance_id" class="card item-card">
        <div class="item-head">
          <span class="item-name" :style="{ color: RARITY[item.rarity] || 'var(--ink-dark)' }">{{ item.name || item.item_id }}</span>
          <span v-if="(item.quantity||1) > 1" class="text-dim">x{{ item.quantity }}</span>
        </div>
        <p v-if="item.desc" class="item-desc">{{ item.desc }}</p>
        <div v-if="item.equipped" class="item-badge">已装备</div>
        <div class="item-actions">
          <button v-if="item.usable" class="btn btn-primary" :disabled="acting" @click="onUse(item)"><IcUse class="icon" /> 使用</button>
          <button v-if="item.equippable && !item.equipped" class="btn btn-ghost" :disabled="acting" @click="onEquip(item)"><IcEquip class="icon" /> 装备</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bag-page { padding: var(--space-lg); padding-bottom: 86px; display: flex; flex-direction: column; gap: var(--space-md); }
.page-title { font-size: 1.05rem; display: flex; align-items: center; gap: var(--space-sm); }
.icon { width: 1rem; height: 1rem; }
.page-loading, .page-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 40vh; color: var(--ink-light); gap: var(--space-sm); }
.msg { text-align: center; font-size: .85rem; cursor: pointer; }

.item-list { display: flex; flex-direction: column; gap: var(--space-sm); }
.item-card { padding: var(--space-md); position: relative; }
.item-head { display: flex; justify-content: space-between; align-items: baseline; }
.item-name { font-weight: 700; font-size: .88rem; }
.item-desc { font-size: .74rem; color: var(--ink-light); margin-top: 2px; }
.item-badge { position: absolute; top: var(--space-sm); right: var(--space-sm); font-size: .6rem; padding: 1px 6px; border-radius: 2px; background: var(--gold); color: #fff; }
.item-actions { display: flex; gap: var(--space-xs); margin-top: var(--space-sm); }
</style>
