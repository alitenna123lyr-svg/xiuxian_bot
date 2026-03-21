/** Player state store */

import { defineStore } from 'pinia'
import { fetchInit, type InitData } from '@/api/client'

interface PlayerState {
  userId: string
  username: string
  rank: number
  exp: number
  copper: number
  gold: number
  hp: number
  maxHp: number
  mp: number
  maxMp: number
  attack: number
  defense: number
  element: string
  currentMap: string
  loaded: boolean
  loading: boolean
  raw: Record<string, any>
}

export const usePlayerStore = defineStore('player', {
  state: (): PlayerState => ({
    userId: '',
    username: '',
    rank: 1,
    exp: 0,
    copper: 0,
    gold: 0,
    hp: 100,
    maxHp: 100,
    mp: 50,
    maxMp: 50,
    attack: 10,
    defense: 5,
    element: '',
    currentMap: 'canglan_city',
    loaded: false,
    loading: false,
    raw: {},
  }),

  getters: {
    hpPercent: (s) => (s.maxHp > 0 ? Math.round((s.hp / s.maxHp) * 100) : 0),
    mpPercent: (s) => (s.maxMp > 0 ? Math.round((s.mp / s.maxMp) * 100) : 0),
    realmName: (s) => REALM_NAMES[s.rank] || `???`,
  },

  actions: {
    setUserId(id: string) {
      this.userId = id
    },

    async init() {
      if (!this.userId || this.loading) return
      this.loading = true
      try {
        const data: InitData = await fetchInit(this.userId)
        this.applyUserData(data.user)
        this.loaded = true
      } finally {
        this.loading = false
      }
    },

    applyUserData(u: Record<string, any>) {
      this.raw = u
      this.username = u.in_game_username || u.username || ''
      this.rank = u.rank || 1
      this.exp = u.exp || 0
      this.copper = u.copper || 0
      this.gold = u.gold || 0
      this.hp = u.hp || 100
      this.maxHp = u.max_hp || 100
      this.mp = u.mp || 50
      this.maxMp = u.max_mp || 50
      this.attack = u.attack || 10
      this.defense = u.defense || 5
      this.element = u.element || ''
      this.currentMap = u.current_map || 'canglan_city'
    },
  },
})

const REALM_NAMES: Record<number, string> = {
  1: '凡人',
  2: '练气一层', 3: '练气二层', 4: '练气三层',
  5: '练气四层', 6: '练气五层', 7: '练气六层',
  8: '筑基初期', 9: '筑基中期', 10: '筑基后期', 11: '筑基圆满',
  12: '金丹初期', 13: '金丹中期', 14: '金丹后期', 15: '金丹圆满',
  16: '元婴初期', 17: '元婴中期', 18: '元婴后期', 19: '元婴圆满',
  20: '化神初期', 21: '化神中期', 22: '化神后期', 23: '化神圆满',
  24: '合体初期', 25: '合体中期', 26: '合体后期', 27: '合体圆满',
  28: '渡劫初期', 29: '渡劫中期', 30: '渡劫后期', 31: '渡劫圆满',
  32: '大乘初期', 33: '大乘中期', 34: '大乘后期', 35: '大乘圆满',
  36: '渡仙劫',
}
