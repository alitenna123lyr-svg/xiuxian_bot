<script setup lang="ts">
import IcShop from '~icons/mdi/store'
import IcFlask from '~icons/mdi/flask-round-bottom'
import { usePlayerStore } from '@/stores/player'
import { getShop, buyItem, getAlchemyRecipes, brew } from '@/api/client'

type Tab = 'shop' | 'alchemy'

const player = usePlayerStore()
const tab = ref<Tab>('shop')
const loading = ref(false)
const msg = ref('')
const acting = ref(false)

// Shop
const shopItems = ref<any[]>([])
// Alchemy
const recipes = ref<any[]>([])

onMounted(async () => {
  if (!player.loaded && player.userId) await player.init()
  await loadTab()
})

watch(tab, loadTab)

async function loadTab() {
  loading.value = true; msg.value = ''
  try {
    if (tab.value === 'shop') {
      const r = await getShop()
      shopItems.value = r.items || r.shop || []
    } else if (tab.value === 'alchemy') {
      const r = await getAlchemyRecipes()
      recipes.value = r.recipes || []
    }
  } catch {} finally { loading.value = false }
}

async function doBuy(item: any) {
  if (acting.value) return
  acting.value = true; msg.value = ''
  try {
    const r = await buyItem(player.userId, item.item_id || item.id)
    msg.value = r.message || '购买成功'
    await player.init(true)
  } catch (e: any) { msg.value = e?.body?.message || '购买失败' }
  finally { acting.value = false }
}

async function doBrew(recipe: any) {
  if (acting.value) return
  acting.value = true; msg.value = ''
  try {
    const r = await brew(player.userId, recipe.recipe_id || recipe.id)
    msg.value = r.message || '炼丹成功'
    await player.init(true)
  } catch (e: any) { msg.value = e?.body?.message || '炼丹失败' }
  finally { acting.value = false }
}

async function doPull(banner: any, count: number) {
  if (acting.value) return
  acting.value = true; msg.value = ''
  try {
    const r = await gachaPull(player.userId, banner.banner_id || banner.id, count)
    pullResult.value = r.results || r.items || []
    msg.value = ''
    await player.init(true)
  } catch (e: any) { msg.value = e?.body?.message || '抽取失败' }
  finally { acting.value = false }
}
</script>

<template>
  <div class="mall-page">
    <!-- tab bar -->
    <div class="tab-bar">
      <button :class="{ active: tab==='shop' }" @click="tab='shop'"><IcShop class="icon" /> 商店</button>
      <button :class="{ active: tab==='alchemy' }" @click="tab='alchemy'"><IcFlask class="icon" /> 炼丹</button>
    </div>

    <p v-if="msg" class="msg card fade-in" @click="msg=''">{{ msg }}</p>

    <div v-if="loading" class="page-loading"><div class="loading-spinner"></div></div>

    <template v-else>
      <!-- shop -->
      <template v-if="tab==='shop'">
        <div v-if="!shopItems.length" class="page-empty"><p>商店暂无商品</p></div>
        <div v-else class="item-list">
          <div v-for="item in shopItems" :key="item.item_id||item.id" class="card item-card" @click="doBuy(item)">
            <div class="item-head">
              <span class="item-name">{{ item.name || item.item_id }}</span>
              <span class="text-gold">{{ item.price || 0 }} 铜</span>
            </div>
            <p v-if="item.desc" class="item-desc">{{ item.desc }}</p>
          </div>
        </div>
      </template>

      <!-- alchemy -->
      <template v-if="tab==='alchemy'">
        <div v-if="!recipes.length" class="page-empty"><p>暂无丹方</p></div>
        <div v-else class="item-list">
          <div v-for="r in recipes" :key="r.recipe_id||r.id" class="card item-card">
            <div class="item-head">
              <span class="item-name">{{ r.name || r.recipe_id }}</span>
              <span class="text-dim" style="font-size:.72rem">{{ r.success_rate ? (r.success_rate*100).toFixed(0)+'%' : '' }}</span>
            </div>
            <p v-if="r.desc" class="item-desc">{{ r.desc }}</p>
            <button class="btn btn-primary" style="margin-top:var(--space-xs)" :disabled="acting" @click="doBrew(r)">炼制</button>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.mall-page { padding: var(--space-lg); padding-bottom: 86px; display: flex; flex-direction: column; gap: var(--space-md); }
.icon { width: 1rem; height: 1rem; }
.tab-bar { display: flex; gap: 0; background: var(--paper-dark); border-radius: var(--radius-md); overflow: hidden; border: 1px solid var(--paper-deeper); }
.tab-bar button { flex: 1; padding: var(--space-sm) 0; font-size: .82rem; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 4px; color: var(--ink-light); transition: all var(--duration-fast); }
.tab-bar button.active { background: var(--paper); color: var(--ink-dark); box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.page-loading, .page-empty { display: flex; align-items: center; justify-content: center; min-height: 40vh; color: var(--ink-light); }
.msg { text-align: center; font-size: .85rem; cursor: pointer; }

.item-list { display: flex; flex-direction: column; gap: var(--space-sm); }
.item-card { padding: var(--space-md); cursor: pointer; transition: background var(--duration-fast); }
.item-card:active { background: var(--paper-dark); }
.item-head { display: flex; justify-content: space-between; align-items: baseline; }
.item-name { font-weight: 700; font-size: .88rem; color: var(--ink-dark); }
.item-desc { font-size: .74rem; color: var(--ink-light); margin-top: 2px; }

.gacha-actions { display: flex; gap: var(--space-sm); margin-top: var(--space-sm); }
.pull-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: var(--space-xs); }
.pull-item { font-size: .82rem; padding: 4px 8px; background: var(--paper-dark); border-radius: var(--radius-sm); }
</style>
