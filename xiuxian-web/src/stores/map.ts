/** Map / travel store */

import { defineStore } from 'pinia'
import { get, travelTo, getAreaActions } from '@/api/client'

export interface MapNode {
  id: string
  name: string
  desc: string
  region: string
  region_name: string
  spirit_density: number
  min_realm: number
  accessible: boolean
  is_current: boolean
  adjacent: string[]
}

export interface AreaAction {
  id: string
  label: string
  icon: string
}

interface MapState {
  maps: MapNode[]
  currentMapId: string
  currentMapName: string
  currentMapDesc: string
  actions: AreaAction[]
  travelResult: Record<string, any> | null
  loading: boolean
}

export const useMapStore = defineStore('map', {
  state: (): MapState => ({
    maps: [],
    currentMapId: 'canglan_city',
    currentMapName: '',
    currentMapDesc: '',
    actions: [],
    travelResult: null,
    loading: false,
  }),

  getters: {
    adjacentMaps: (s) => s.maps.filter(m => {
      const current = s.maps.find(c => c.id === s.currentMapId)
      return current?.adjacent?.includes(m.id) && m.accessible
    }),
    regionGroups: (s) => {
      const groups: Record<string, MapNode[]> = {}
      for (const m of s.maps) {
        const key = m.region_name || m.region || 'unknown'
        if (!groups[key]) groups[key] = []
        groups[key].push(m)
      }
      return groups
    },
  },

  actions: {
    setCurrentMap(mapId: string) {
      this.currentMapId = mapId
      const m = this.maps.find(n => n.id === mapId)
      if (m) {
        this.currentMapName = m.name
        this.currentMapDesc = m.desc
      }
    },

    async fetchActions() {
      if (!this.currentMapId) return
      try {
        const r = await getAreaActions(this.currentMapId)
        this.actions = r.actions || []
      } catch { this.actions = [] }
    },

    async travel(userId: string, toMapId: string) {
      this.loading = true
      try {
        const r = await travelTo(userId, toMapId)
        this.travelResult = r
        if (r.success) {
          this.setCurrentMap(toMapId)
          await this.fetchActions()
        }
        return r
      } finally { this.loading = false }
    },
  },
})
