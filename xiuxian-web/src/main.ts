import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/global.css'

import { usePlayerStore } from './stores/player'
import { getTwaUser } from './api/client'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

// ── Bootstrap: detect user from Telegram WebApp ──
const twaUser = getTwaUser()
if (twaUser) {
  const player = usePlayerStore()
  // Use Telegram user ID as the lookup key
  // The backend will need a mapping from telegram_id → user_id
  player.setUserId(String(twaUser.id))
  player.init()
}
