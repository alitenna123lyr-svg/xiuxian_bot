/** API client – wraps fetch with Telegram MiniApp auth */

const BASE = import.meta.env.VITE_API_BASE || ''

/** Telegram WebApp instance (injected by TWA runtime) */
function getTwa(): any {
  return (window as any).Telegram?.WebApp
}

/** Get Telegram initData for server-side auth */
export function getTwaInitData(): string {
  return getTwa()?.initData || ''
}

export function getTwaUser(): { id: number; first_name: string } | null {
  return getTwa()?.initDataUnsafe?.user || null
}

/** Typed fetch wrapper */
async function request<T = any>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${BASE}${path}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  // Attach TWA auth
  const initData = getTwaInitData()
  if (initData) {
    headers['X-Telegram-Init-Data'] = initData
  }

  const res = await fetch(url, { ...options, headers })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw Object.assign(new Error(body.message || res.statusText), {
      status: res.status,
      body,
    })
  }
  return res.json()
}

/** GET */
export function get<T = any>(path: string): Promise<T> {
  return request<T>(path)
}

/** POST */
export function post<T = any>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    body: body != null ? JSON.stringify(body) : undefined,
  })
}

// ── Game API calls ──────────────────────────────

export interface InitData {
  user: Record<string, any>
  equipment: Record<string, any>
  skills: any[]
  story: { pending_claims: any[]; available_chapters: any[] }
  quests: any[]
}

/** Batch init – one request to get everything */
export async function fetchInit(userId: string): Promise<InitData> {
  const [stat, story] = await Promise.all([
    get(`/api/stat/${userId}`),
    get(`/api/story/volumes/${userId}`),
  ])
  return {
    user: stat.status || {},
    equipment: {},
    skills: [],
    story: {
      pending_claims: [],
      available_chapters: story.available_chapters || [],
    },
    quests: [],
  }
}

/** Story: read next lines */
export function storyRead(userId: string, chapterId: string, count = 5) {
  return post('/api/story/read', { user_id: userId, chapter_id: chapterId, count })
}

/** Story: reset chapter */
export function storyReread(userId: string, chapterId: string) {
  return post('/api/story/reread', { user_id: userId, chapter_id: chapterId })
}
