/** Story store – manages chapter list and reading progress */

import { defineStore } from 'pinia'
import { get, storyRead, storyReread } from '@/api/client'

export interface StoryLine {
  type: 'narration' | 'dialogue' | 'choice'
  text: string
  speaker?: string
}

export interface ChapterEntry {
  chapter_id: string
  title: string
  volume_title: string
  current_line: number
  total_lines: number
  is_new: boolean
}

interface StoryState {
  chapters: ChapterEntry[]
  /** Currently reading chapter */
  activeChapterId: string
  activeTitle: string
  activeVolumeTitle: string
  /** Lines already displayed (cumulative) */
  displayedLines: StoryLine[]
  currentLine: number
  totalLines: number
  isFinished: boolean
  loading: boolean
}

export const useStoryStore = defineStore('story', {
  state: (): StoryState => ({
    chapters: [],
    activeChapterId: '',
    activeTitle: '',
    activeVolumeTitle: '',
    displayedLines: [],
    currentLine: 0,
    totalLines: 0,
    isFinished: false,
    loading: false,
  }),

  actions: {
    async fetchChapters(userId: string) {
      this.loading = true
      try {
        const res = await get(`/api/story/volumes/${userId}`)
        this.chapters = res.available_chapters || []
      } finally {
        this.loading = false
      }
    },

    async readNext(userId: string, chapterId: string) {
      this.loading = true
      try {
        const res = await storyRead(userId, chapterId, 5)
        if (!res.success) return

        this.activeChapterId = chapterId
        this.activeTitle = res.title || ''
        this.activeVolumeTitle = res.volume_title || ''
        this.currentLine = res.current_line
        this.totalLines = res.total_lines
        this.isFinished = res.is_finished

        // Append new lines to displayed (for scroll-down effect)
        const newLines: StoryLine[] = res.lines || []
        this.displayedLines.push(...newLines)
      } finally {
        this.loading = false
      }
    },

    async rereadChapter(userId: string, chapterId: string) {
      this.loading = true
      try {
        await storyReread(userId, chapterId)
        // Reset local state
        this.displayedLines = []
        this.currentLine = 0
        this.isFinished = false
        // Read from beginning
        await this.readNext(userId, chapterId)
      } finally {
        this.loading = false
      }
    },

    startReading(chapterId: string) {
      this.activeChapterId = chapterId
      this.displayedLines = []
      this.currentLine = 0
      this.totalLines = 0
      this.isFinished = false
    },
  },
})
