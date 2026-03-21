<script setup lang="ts">
/** 剧情页 – 章节列表 + 阅读器 */
import StoryLineComp from '@/components/StoryLine.vue'
import { usePlayerStore } from '@/stores/player'
import { useStoryStore, type StoryLine } from '@/stores/story'

const player = usePlayerStore()
const story = useStoryStore()
const route = useRoute()
const router = useRouter()

// If a chapter_id is in the route, go directly to reading mode
const readingChapterId = ref(route.query.ch as string || '')

const scrollBox = ref<HTMLElement | null>(null)

// Index of the newest line currently being animated
const animatingIndex = ref(-1)

onMounted(async () => {
  if (player.userId) {
    await story.fetchChapters(player.userId)
    if (readingChapterId.value) {
      await startReading(readingChapterId.value)
    }
  }
})

async function startReading(chapterId: string) {
  readingChapterId.value = chapterId
  story.startReading(chapterId)
  await loadMore()
}

async function loadMore() {
  if (!readingChapterId.value || !player.userId) return
  const prevCount = story.displayedLines.length
  await story.readNext(player.userId, readingChapterId.value)

  // Animate only newly added lines
  if (story.displayedLines.length > prevCount) {
    animatingIndex.value = prevCount
  }

  // Scroll to bottom after a short delay
  await nextTick()
  setTimeout(() => {
    scrollBox.value?.scrollTo({
      top: scrollBox.value.scrollHeight,
      behavior: 'smooth',
    })
  }, 100)
}

async function reread() {
  if (!readingChapterId.value || !player.userId) return
  animatingIndex.value = -1
  await story.rereadChapter(player.userId, readingChapterId.value)
  animatingIndex.value = 0
}

function backToList() {
  readingChapterId.value = ''
  story.fetchChapters(player.userId)
}

function onLineDone() {
  // Move animation pointer to next line
  if (animatingIndex.value >= 0 && animatingIndex.value < story.displayedLines.length - 1) {
    animatingIndex.value++
  }
}
</script>

<template>
  <div class="story-page">
    <!-- ── Chapter list ── -->
    <template v-if="!readingChapterId">
      <div class="story-page__header">
        <h2>📜 主线剧情</h2>
      </div>

      <div v-if="story.loading" class="story-page__loading">
        <div class="loading-spinner"></div>
      </div>

      <div v-else-if="story.chapters.length === 0" class="story-page__empty">
        <p>暂无可阅读的章节</p>
        <p class="text-dim">继续修炼以解锁更多剧情</p>
      </div>

      <div v-else class="chapter-list">
        <div
          v-for="ch in story.chapters"
          :key="ch.chapter_id"
          class="chapter-item card"
          @click="startReading(ch.chapter_id)"
        >
          <div class="chapter-item__left">
            <span class="chapter-item__badge" :class="{
              'chapter-item__badge--new': ch.is_new,
              'chapter-item__badge--reading': ch.current_line > 0 && ch.current_line < ch.total_lines,
              'chapter-item__badge--done': ch.current_line >= ch.total_lines && ch.total_lines > 0,
            }">
              {{ ch.current_line >= ch.total_lines && ch.total_lines > 0 ? '✅' : ch.is_new ? '🆕' : ch.current_line > 0 ? '📖' : '📕' }}
            </span>
            <div>
              <div class="chapter-item__volume">{{ ch.volume_title }}</div>
              <div class="chapter-item__title">{{ ch.title }}</div>
            </div>
          </div>
          <div class="chapter-item__progress">
            {{ ch.current_line >= ch.total_lines && ch.total_lines > 0 ? '已读' : ch.current_line > 0 ? `${ch.current_line}/${ch.total_lines}` : '未读' }}
          </div>
        </div>
      </div>
    </template>

    <!-- ── Reading mode ── -->
    <template v-else>
      <div class="reader">
        <div class="reader__header">
          <button class="btn btn-ghost" @click="backToList">← 返回</button>
          <div class="reader__title">
            <div class="reader__volume">{{ story.activeVolumeTitle }}</div>
            <div class="reader__chapter">{{ story.activeTitle }}</div>
          </div>
          <div class="reader__progress">{{ story.currentLine }}/{{ story.totalLines }}</div>
        </div>

        <div ref="scrollBox" class="reader__body">
          <StoryLineComp
            v-for="(line, idx) in story.displayedLines"
            :key="`${story.activeChapterId}-${idx}`"
            :type="line.type"
            :text="line.text"
            :speaker="line.speaker"
            :animate="idx >= animatingIndex"
            :style="{ animationDelay: idx >= animatingIndex ? `${(idx - animatingIndex) * 0.15}s` : '0s' }"
            @done="onLineDone"
          />

          <div v-if="story.loading" class="reader__loading">
            <div class="loading-spinner"></div>
          </div>
        </div>

        <div class="reader__footer">
          <template v-if="!story.isFinished">
            <button class="btn btn-primary btn-block" @click="loadMore" :disabled="story.loading">
              ▶️ 继续阅读
            </button>
          </template>
          <template v-else>
            <div class="reader__finished">— 本章完 —</div>
            <div class="reader__actions">
              <button class="btn btn-ghost" @click="reread">🔄 重读</button>
              <button class="btn btn-primary" @click="backToList">📜 章节列表</button>
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.story-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  height: calc(100dvh - 60px);
}

.story-page__header {
  padding: var(--space-lg);
  padding-bottom: var(--space-sm);
}

.story-page__header h2 {
  font-size: 1.1rem;
  color: var(--color-text-bright);
}

.story-page__loading,
.story-page__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: var(--space-sm);
  color: var(--color-text-dim);
}

.text-dim {
  font-size: 0.8rem;
  color: var(--color-text-dim);
}

/* ── Chapter list ── */

.chapter-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 var(--space-lg) 80px;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.chapter-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  cursor: pointer;
  transition: background var(--duration-fast);
  -webkit-tap-highlight-color: transparent;
}

.chapter-item:active {
  background: var(--color-bg-card-hover);
}

.chapter-item__left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.chapter-item__badge {
  font-size: 1.2rem;
  width: 32px;
  text-align: center;
}

.chapter-item__volume {
  font-size: 0.65rem;
  color: var(--color-text-dim);
}

.chapter-item__title {
  font-size: 0.85rem;
  color: var(--color-text-bright);
  font-weight: 500;
}

.chapter-item__progress {
  font-size: 0.7rem;
  color: var(--color-text-dim);
  white-space: nowrap;
}

/* ── Reader ── */

.reader {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.reader__header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-card);
  flex-shrink: 0;
}

.reader__title {
  flex: 1;
  text-align: center;
}

.reader__volume {
  font-size: 0.6rem;
  color: var(--color-text-dim);
}

.reader__chapter {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-bright);
}

.reader__progress {
  font-size: 0.7rem;
  color: var(--color-text-dim);
  font-family: var(--font-mono);
}

.reader__body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
  scroll-behavior: smooth;
}

.reader__loading {
  display: flex;
  justify-content: center;
  padding: var(--space-lg);
}

.reader__footer {
  padding: var(--space-md) var(--space-lg);
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-card);
  flex-shrink: 0;
  padding-bottom: calc(var(--space-md) + env(safe-area-inset-bottom, 0px));
}

.reader__finished {
  text-align: center;
  color: var(--color-accent);
  font-size: 0.85rem;
  margin-bottom: var(--space-sm);
}

.reader__actions {
  display: flex;
  gap: var(--space-sm);
  justify-content: center;
}
</style>
