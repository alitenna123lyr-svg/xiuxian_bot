<script setup lang="ts">
/**
 * WorldMap – 水墨大地图
 * 按区域分组显示地图节点，当前位置高亮，点击可移动
 */
import { usePlayerStore } from '@/stores/player'
import { useMapStore } from '@/stores/map'
import { get } from '@/api/client'

const player = usePlayerStore()
const map = useMapStore()
const router = useRouter()

const travelMsg = ref('')
const showTravel = ref(false)

onMounted(async () => {
  if (!player.userId) return
  map.setCurrentMap(player.currentMap)
  await map.fetchActions()
  // Load map list from backend
  try {
    const r = await get(`/api/stat/${player.userId}`)
    if (r.success && r.status) {
      map.setCurrentMap(r.status.current_map || 'canglan_city')
    }
  } catch {}
})

async function doTravel(toMapId: string) {
  if (!player.userId) return
  showTravel.value = false
  const r = await map.travel(player.userId, toMapId)
  if (r?.success) {
    player.currentMap = toMapId
    travelMsg.value = ''
    if (r.first_visit && r.first_visit_text) {
      travelMsg.value = r.first_visit_text
      showTravel.value = true
    }
  } else {
    travelMsg.value = r?.message || '无法前往'
    showTravel.value = true
  }
}

// Map region data (static, matches core/game/maps.py)
const regions = [
  {
    name: '苍澜洲',
    desc: '灵气稀薄的东南大陆，修行者的起点',
    maps: [
      { id: 'canglan_city', name: '苍澜城', icon: '🏯', minRank: 1 },
      { id: 'east_forest', name: '东郊灵林', icon: '🌲', minRank: 1 },
      { id: 'south_market', name: '南市坊市', icon: '🏪', minRank: 1 },
      { id: 'north_mountain', name: '北望灵山', icon: '⛰️', minRank: 2 },
      { id: 'fallen_star_lake', name: '落星湖', icon: '🌊', minRank: 3 },
      { id: 'luoxia_valley', name: '落霞谷', icon: '🏔️', minRank: 4 },
      { id: 'canglan_mines', name: '苍澜矿脉', icon: '⛏️', minRank: 3 },
      { id: 'misty_swamp', name: '迷雾沼泽', icon: '🌫️', minRank: 5 },
    ],
  },
  {
    name: '天渊洲',
    desc: '宗门林立的中央大陆',
    maps: [
      { id: 'tianyuan_sect_city', name: '天元宗城', icon: '🏛️', minRank: 6 },
      { id: 'sword_peak', name: '万剑峰', icon: '⚔️', minRank: 8 },
      { id: 'pill_pavilion', name: '丹鼎阁', icon: '🧪', minRank: 7 },
      { id: 'chaos_sea', name: '乱星海', icon: '🌊', minRank: 8 },
      { id: 'ancient_battlefield', name: '古战场', icon: '💀', minRank: 10 },
    ],
  },
  {
    name: '逆墟',
    desc: '逆道修士的聚集之地',
    maps: [
      { id: 'nixu_city', name: '逆墟城', icon: '🌑', minRank: 18 },
      { id: 'blood_abyss', name: '血渊', icon: '🩸', minRank: 20 },
      { id: 'fate_rift', name: '命运裂隙', icon: '🌀', minRank: 22 },
    ],
  },
  {
    name: '星陨海',
    desc: '星辰碎片散布的神秘海域',
    maps: [
      { id: 'star_fall_sea', name: '星陨之海', icon: '⭐', minRank: 14 },
      { id: 'star_temple', name: '星辰神殿', icon: '🌟', minRank: 20 },
      { id: 'void_edge', name: '虚空之缘', icon: '🕳️', minRank: 24 },
    ],
  },
]

function isAccessible(minRank: number) {
  return player.rank >= minRank
}

function isCurrent(mapId: string) {
  return mapId === map.currentMapId
}
</script>

<template>
  <div class="wm">
    <div class="wm__header">
      <h2>🗺️ 天元大陆</h2>
      <div class="wm__loc">
        📍 {{ map.currentMapName || map.currentMapId }}
      </div>
    </div>

    <!-- 移动提示 -->
    <Transition name="page">
      <div v-if="showTravel" class="card wm__msg fade-in" @click="showTravel = false">
        <p>{{ travelMsg }}</p>
        <span class="text-dim" style="font-size:0.7rem">点击关闭</span>
      </div>
    </Transition>

    <!-- 区域列表 -->
    <div class="wm__regions">
      <div v-for="region in regions" :key="region.name" class="wm__region card">
        <div class="wm__region-head">
          <h3>{{ region.name }}</h3>
          <span class="text-dim" style="font-size:0.7rem">{{ region.desc }}</span>
        </div>
        <div class="wm__nodes">
          <button
            v-for="m in region.maps" :key="m.id"
            class="wm__node"
            :class="{
              'wm__node--current': isCurrent(m.id),
              'wm__node--locked': !isAccessible(m.minRank),
              'wm__node--open': isAccessible(m.minRank) && !isCurrent(m.id),
            }"
            :disabled="!isAccessible(m.minRank) || isCurrent(m.id)"
            @click="doTravel(m.id)"
          >
            <span class="wm__node-icon">{{ isCurrent(m.id) ? '📍' : !isAccessible(m.minRank) ? '🔒' : m.icon }}</span>
            <span class="wm__node-name">{{ m.name }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 当前区域操作 -->
    <div v-if="map.actions.length" class="card wm__actions">
      <h3 style="font-size:0.85rem;margin-bottom:var(--space-sm)">当前区域可执行</h3>
      <div class="wm__action-grid">
        <button
          v-for="a in map.actions" :key="a.id"
          class="btn btn-ghost"
          @click="router.push(a.id === 'cultivate_bonus' ? '/cultivate' : '/')"
        >
          {{ a.icon || '▸' }} {{ a.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wm { padding: var(--space-lg); padding-bottom: 80px; }
.wm__header { margin-bottom: var(--space-lg); }
.wm__header h2 { font-size: 1.1rem; }
.wm__loc { font-size: 0.8rem; color: var(--gold); margin-top: 2px; }
.wm__msg { margin-bottom: var(--space-md); cursor: pointer; font-size: 0.85rem; line-height: 1.8; }

.wm__regions { display: flex; flex-direction: column; gap: var(--space-md); }
.wm__region { padding: var(--space-md); }
.wm__region-head { margin-bottom: var(--space-sm); }
.wm__region-head h3 { font-size: 0.9rem; }

.wm__nodes { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-xs); }
.wm__node {
  display: flex; align-items: center; gap: var(--space-sm);
  padding: var(--space-sm); border-radius: var(--radius-sm);
  font-size: 0.8rem; font-weight: 500; text-align: left;
  transition: all var(--duration-fast);
  border: 1px solid transparent;
  -webkit-tap-highlight-color: transparent;
}
.wm__node--current {
  background: rgba(184,134,11,0.1); border-color: var(--gold); color: var(--gold);
  font-weight: 700;
}
.wm__node--open { color: var(--ink-dark); }
.wm__node--open:active { background: var(--paper-dark); }
.wm__node--locked { color: var(--ink-faint); opacity: 0.5; cursor: not-allowed; }
.wm__node-icon { font-size: 1.1rem; width: 24px; text-align: center; }
.wm__node-name { flex: 1; }

.wm__actions { margin-top: var(--space-md); }
.wm__action-grid { display: flex; flex-wrap: wrap; gap: var(--space-xs); }
</style>
