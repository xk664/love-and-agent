<template>
  <aside class="session-panel">
    <!-- Header -->
    <div class="panel-header">
      <h2 class="panel-title">对话列表</h2>
      <button class="btn-new" @click="$emit('create')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12h14" />
        </svg>
        <span>新建</span>
      </button>
    </div>

    <!-- Session List -->
    <div class="session-list" ref="listRef" @scroll="handleScroll">
      <div
        v-for="session in sessions"
        :key="getId(session)"
        class="session-item"
        :class="{ active: getId(session) === activeId }"
        @click="$emit('select', session)"
      >
        <div class="session-icon" :class="getTypeClass(session)">
          {{ getTypeIcon(session) }}
        </div>
        <div class="session-info">
          <span class="session-title">{{ session.title || '新对话' }}</span>
          <span class="session-time">{{ formatTime(getTime(session)) }}</span>
        </div>
        <button
          class="session-delete"
          @click.stop="confirmDelete(session)"
          title="删除对话"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
          </svg>
        </button>
      </div>

      <!-- Loading more -->
      <div v-if="loadingMore" class="loading-more">
        <span class="loading-dot" />
        加载中...
      </div>

      <!-- Empty state -->
      <div v-if="sessions.length === 0 && !loading" class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
          </svg>
        </div>
        <p class="empty-text">{{ emptyText }}</p>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useChatStore } from '@/stores/chat'

const props = defineProps({
  sessions: { type: Array, default: () => [] },
  activeId: { type: [String, Number, null], default: null },
  appType: { type: String, default: '' },
  emptyText: { type: String, default: '还没有对话，开始第一次聊天吧' },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['create', 'select', 'delete'])

const chatStore = useChatStore()
const listRef = ref(null)
const loadingMore = ref(false)
const page = ref(1)
const hasMore = ref(true)

// ---- Helpers ----
function getId(s) {
  return s.chat_id || s.id
}

function getTime(s) {
  return s.lastMessageTime || s.last_message_time || s.updatedAt || s.updated_at
}

function formatTime(time) {
  if (!time) return ''
  const d = new Date(time)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) {
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
  }
  const days = Math.floor((now - d) / (1000 * 60 * 60 * 24))
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function getTypeIcon(session) {
  const type = session.appType || session.app_type
  return type === 'love_app' ? '♡' : '◈'
}

function getTypeClass(session) {
  const type = session.appType || session.app_type
  return type === 'love_app' ? 'type-love' : type === 'manus' ? 'type-agent' : ''
}

// ---- Delete ----
async function confirmDelete(session) {
  const title = session.title || '新对话'
  try {
    await ElMessageBox.confirm(
      `确定删除「${title}」？删除后不可恢复。`,
      '删除对话',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    emit('delete', session)
  } catch {
    // cancelled
  }
}

// ---- Infinite Scroll ----
async function handleScroll() {
  const el = listRef.value
  if (!el || loadingMore.value || !hasMore.value) return

  const threshold = 60
  const isBottom = el.scrollHeight - el.scrollTop - el.clientHeight < threshold

  if (isBottom) {
    loadingMore.value = true
    page.value++
    try {
      const params = { page: page.value, page_size: 20 }
      if (props.appType) params.app_type = props.appType
      await chatStore.fetchSessions(params)
      if (chatStore.sessions.length < page.value * 20) {
        hasMore.value = false
      }
    } finally {
      loadingMore.value = false
    }
  }
}
</script>

<style scoped>
.session-panel {
  width: 260px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ---- Header ---- */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border-light);
}

.panel-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
}

.btn-new {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  background: var(--color-primary);
  color: white;
  border-radius: var(--border-radius);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  transition: all var(--duration-fast);
}

.btn-new:hover {
  background: var(--color-primary-light);
  transform: translateY(-1px);
}

.btn-new svg {
  width: 14px;
  height: 14px;
}

/* ---- List ---- */
.session-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2);
}

.session-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all var(--duration-fast);
  position: relative;
}

.session-item:hover {
  background: var(--color-surface-hover);
}

.session-item:hover .session-delete {
  opacity: 1;
}

.session-item.active {
  background: var(--color-accent-bg);
}

.session-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  flex-shrink: 0;
}

.session-icon.type-love {
  background: linear-gradient(135deg, #fdf2f8, #fce7f3);
  color: #ec4899;
}

.session-icon.type-agent {
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  color: #3b82f6;
}

.session-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.session-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: var(--text-xs);
  color: var(--color-ink-faint);
}

/* ---- Delete ---- */
.session-delete {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius);
  color: var(--color-ink-faint);
  opacity: 0;
  transition: all var(--duration-fast);
  flex-shrink: 0;
}

.session-delete:hover {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.session-delete svg {
  width: 14px;
  height: 14px;
}

/* ---- Loading More ---- */
.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-4);
  font-size: var(--text-xs);
  color: var(--color-ink-muted);
}

.loading-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-ink-muted);
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

/* ---- Empty State ---- */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-12) var(--space-4);
  gap: var(--space-3);
}

.empty-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-hover);
  color: var(--color-ink-faint);
  border-radius: 50%;
  opacity: 0.5;
}

.empty-icon svg {
  width: 24px;
  height: 24px;
}

.empty-text {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  text-align: center;
  line-height: var(--leading-relaxed);
}

/* ---- Responsive ---- */
@media (max-width: 768px) {
  .session-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--color-border);
  }
}
</style>
