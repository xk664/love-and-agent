<template>
  <aside class="session-panel">
    <!-- Header -->
    <div class="panel-header">
      <button class="btn-new" :class="accent" @click="$emit('create')">
        <span class="btn-new-icon">+</span>
        <span>新建对话</span>
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
        <div class="session-main">
          <span class="session-title">{{ session.title || '新对话' }}</span>
          <span class="session-time">{{ formatTime(getTime(session)) }}</span>
        </div>

        <!-- App type tag -->
        <span v-if="showTypeTag" class="session-tag" :class="getTypeClass(session)">
          {{ getTypeLabel(session) }}
        </span>

        <!-- Delete button -->
        <button
          class="btn-delete"
          @click.stop="confirmDelete(session)"
          title="删除对话"
        >
          ✕
        </button>
      </div>

      <!-- Loading more -->
      <div v-if="loadingMore" class="loading-more">
        <span class="loading-dot" />
        加载中...
      </div>

      <!-- Empty state -->
      <div v-if="sessions.length === 0 && !loading" class="empty-state">
        <div class="empty-icon">{{ emptyIcon }}</div>
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
  accent: { type: String, default: '' },          // 'coral' | 'indigo'
  appType: { type: String, default: '' },          // filter for fetching
  showTypeTag: { type: Boolean, default: false },   // show app_type badge
  emptyIcon: { type: String, default: '☰' },
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
  return s.chatId || s.chat_id || s.id
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
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function getTypeLabel(session) {
  const type = session.appType || session.app_type
  return type === 'love_app' ? '恋爱大师' : type === 'manus' ? '智能体' : type
}

function getTypeClass(session) {
  const type = session.appType || session.app_type
  return type === 'love_app' ? 'tag-coral' : type === 'manus' ? 'tag-indigo' : ''
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
  background: var(--color-cloud);
  border-right: 1px solid var(--color-stone-bg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ---- Header ---- */
.panel-header {
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-stone-bg);
}

.btn-new {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  transition: all var(--duration-fast);
}

.btn-new.coral {
  background: var(--color-coral-bg);
  color: var(--color-coral);
}
.btn-new.coral:hover {
  background: var(--color-coral);
  color: white;
}

.btn-new.indigo {
  background: var(--color-indigo-bg);
  color: var(--color-indigo);
}
.btn-new.indigo:hover {
  background: var(--color-indigo);
  color: white;
}

.btn-new:not(.coral):not(.indigo) {
  background: var(--color-stone-bg);
  color: var(--color-ink-muted);
}
.btn-new:not(.coral):not(.indigo):hover {
  background: var(--color-ink-muted);
  color: white;
}

.btn-new-icon {
  font-size: var(--text-lg);
  line-height: 1;
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
  gap: var(--space-2);
  padding: var(--space-3) var(--space-3);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all var(--duration-fast);
  position: relative;
}

.session-item:hover {
  background: var(--color-mist);
}

.session-item:hover .btn-delete {
  opacity: 1;
}

.session-item.active {
  background: var(--color-stone-bg);
}

.session-item.active.coral-active {
  background: var(--color-coral-bg);
}

.session-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.session-title {
  font-size: var(--text-sm);
  color: var(--color-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: var(--text-xs);
  color: var(--color-stone);
}

/* ---- Type Tag ---- */
.session-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: var(--border-radius-full);
  font-weight: var(--weight-medium);
  flex-shrink: 0;
}

.tag-coral {
  background: var(--color-coral-bg);
  color: var(--color-coral);
}

.tag-indigo {
  background: var(--color-indigo-bg);
  color: var(--color-indigo);
}

/* ---- Delete ---- */
.btn-delete {
  opacity: 0;
  color: var(--color-stone);
  font-size: var(--text-xs);
  padding: var(--space-1);
  border-radius: var(--border-radius);
  transition: all var(--duration-fast);
  flex-shrink: 0;
}

.btn-delete:hover {
  color: var(--color-danger);
  background: rgba(239, 68, 68, 0.08);
}

/* ---- Loading More ---- */
.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-4);
  font-size: var(--text-xs);
  color: var(--color-stone);
}

.loading-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-stone);
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
  font-size: 32px;
  color: var(--color-stone-light);
}

.empty-text {
  font-size: var(--text-sm);
  color: var(--color-stone);
  text-align: center;
  line-height: var(--leading-relaxed);
}

/* ---- Responsive ---- */
@media (max-width: 768px) {
  .session-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--color-stone-bg);
  }
}
</style>
