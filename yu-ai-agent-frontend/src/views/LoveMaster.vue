<template>
  <div class="love-master">
    <!-- Header -->
    <header class="page-header">
      <div class="header-left">
        <button class="btn-back" @click="$router.push('/')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <!-- Mobile: toggle session panel -->
        <button class="btn-toggle-panel" @click="panelOpen = !panelOpen">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18M3 12h18M3 18h18" />
          </svg>
        </button>
        <div class="header-info">
          <h1 class="page-title">恋爱大师</h1>
          <p class="page-subtitle">温暖陪伴，理解你的每一种心情</p>
        </div>
      </div>
      <div class="header-status">
        <span class="status-dot" />
        <span>在线</span>
      </div>
    </header>

    <div class="chat-container">
      <!-- Mobile Overlay -->
      <div v-if="panelOpen" class="panel-overlay" @click="panelOpen = false" />

      <!-- Session Panel -->
      <aside class="session-panel" :class="{ open: panelOpen }">
        <div class="panel-header">
          <h2 class="panel-title">对话列表</h2>
          <button class="btn-new" @click="showCreateDialog = true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
            <span>新建</span>
          </button>
        </div>

        <div class="session-list" v-if="chatStore.sessions.length > 0">
          <button
            v-for="session in chatStore.sessions"
            :key="session.chat_id"
            class="session-item"
            :class="{ active: chatStore.currentChatId === session.chat_id }"
            @click="selectSession(session)"
          >
            <div class="session-icon">♡</div>
            <div class="session-info">
              <span class="session-title">{{ session.title || '新对话' }}</span>
              <span class="session-time">{{ formatRelativeTime(session.createTime) }}</span>
            </div>
            <button
              class="session-delete"
              @click.stop="handleDelete(session)"
              title="删除对话"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
              </svg>
            </button>
          </button>
        </div>

        <div class="panel-empty" v-else>
          <div class="empty-icon">♡</div>
          <p>还没有对话</p>
          <button class="btn-create" @click="showCreateDialog = true">开始新对话</button>
        </div>
      </aside>

      <!-- Main Chat Area -->
      <main class="chat-main">
        <!-- No session selected -->
        <div v-if="!chatStore.currentChatId" class="no-session">
          <div class="no-session-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </div>
          <h3>选择一个对话</h3>
          <p>从左侧选择已有对话，或创建新的对话</p>
        </div>

        <!-- Active chat -->
        <template v-else>
          <!-- Messages area -->
          <div class="messages-area" ref="messagesRef">
            <!-- Welcome (empty chat) -->
            <div v-if="displayMessages.length === 0 && !chatStore.streaming" class="welcome">
              <div class="welcome-avatar">
                <div class="avatar-large">♡</div>
              </div>
              <h3>你好，我是恋爱大师</h3>
              <p class="welcome-desc">无论什么心情，都可以和我聊聊。我会用心倾听，给你温暖的建议。</p>
              <div class="starters">
                <button
                  v-for="s in starters"
                  :key="s"
                  class="starter-chip"
                  @click="useStarter(s)"
                >
                  {{ s }}
                </button>
              </div>
            </div>

            <!-- Message list -->
            <template v-for="msg in displayMessages" :key="msg.id || msg._key">
              <!-- User message -->
              <div v-if="msg.role === 'user'" class="message-row user-row">
                <div class="bubble user-bubble">
                  <div class="bubble-text">{{ msg.content }}</div>
                  <div class="bubble-time">{{ formatTime(msg.createTime) }}</div>
                </div>
              </div>

              <!-- Assistant message -->
              <div v-else class="message-row assistant-row">
                <div class="avatar-sm">♡</div>
                <div class="bubble assistant-bubble">
                  <div class="bubble-text">
                    <MarkdownRenderer :content="msg.content" />
                  </div>

                  <!-- RAG Sources toggle -->
                  <div v-if="hasRagSources(msg)" class="metadata-area">
                    <button
                      class="metadata-toggle"
                      :class="{ expanded: msg._metaOpen }"
                      @click="toggleMetadata(msg)"
                    >
                      <svg class="meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="16" y1="13" x2="8" y2="13" />
                        <line x1="16" y1="17" x2="8" y2="17" />
                        <polyline points="10 9 9 9 8 9" />
                      </svg>
                      <span>{{ msg._metaOpen ? '收起来源' : '查看来源' }}</span>
                    </button>
                    <div v-if="msg._metaOpen" class="metadata-detail">
                      <div class="meta-section">
                        <span class="meta-label">参考来源</span>
                        <div
                          v-for="(src, i) in getRagSources(msg)"
                          :key="i"
                          class="meta-source"
                        >
                          <span class="source-name">{{ getSourceTitle(src, i) }}</span>
                          <span v-if="src.score" class="source-score">{{ (src.score * 100).toFixed(0) }}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <!-- Thinking indicator -->
            <div v-if="chatStore.streaming && !chatStore.streamingContent" class="message-row assistant-row">
              <div class="avatar-sm">♡</div>
              <div class="bubble assistant-bubble thinking-bubble">
                <div class="thinking-dots">
                  <span class="dot" />
                  <span class="dot" />
                  <span class="dot" />
                </div>
                <span class="thinking-text">思考中</span>
              </div>
            </div>

            <!-- Streaming message -->
            <div v-if="chatStore.streamingContent" class="message-row assistant-row">
              <div class="avatar-sm">♡</div>
              <div class="bubble assistant-bubble">
                <div class="bubble-text streaming-text">
                  <MarkdownRenderer :content="chatStore.streamingContent" /><span class="cursor" />
                </div>
              </div>
            </div>
          </div>

          <!-- Input area -->
          <div class="input-area">
            <div class="input-wrapper">
              <textarea
                ref="inputRef"
                v-model="inputText"
                class="chat-input"
                placeholder="说说你的心情..."
                rows="1"
                :disabled="chatStore.streaming"
                @keydown="handleKeydown"
                @input="autoResize"
              />
              <div class="input-actions">
                <button
                  v-if="chatStore.streaming"
                  class="btn-stop"
                  @click="chatStore.cancelStream()"
                >
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="6" width="12" height="12" rx="2" />
                  </svg>
                  停止
                </button>
                <button
                  v-else
                  class="btn-send"
                  :disabled="!inputText.trim()"
                  @click="sendMessage"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 2L11 13" />
                    <path d="M22 2L15 22L11 13L2 9L22 2Z" />
                  </svg>
                </button>
              </div>
            </div>
            <div class="input-hint">
              <span v-if="chatStore.streaming" class="hint-streaming">
                AI 正在回复中...
              </span>
              <span v-else class="hint-default">
                Enter 发送 · Shift+Enter 换行
              </span>
            </div>
          </div>
        </template>
      </main>
    </div>

    <!-- Create Session Dialog -->
    <CreateSessionDialog
      :visible="showCreateDialog"
      default-type="love_app"
      @close="showCreateDialog = false"
      @created="onSessionCreated"
    />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import CreateSessionDialog from '@/components/CreateSessionDialog.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

const chatStore = useChatStore()
const inputText = ref('')
const showCreateDialog = ref(false)
const messagesRef = ref(null)
const inputRef = ref(null)
const panelOpen = ref(false)
let messageKeyCounter = 0

// Suggested conversation starters
const starters = [
  '最近感情不太顺利，想聊聊',
  '怎么判断一个人是不是喜欢我',
  '异地恋好难，有什么建议吗',
  '刚分手，不知道该怎么办'
]

// ---- Messages list (使用 computed 保持响应性) ----
const displayMessages = computed(() => chatStore.messages)

// ---- Lifecycle ----
onMounted(() => {
  // 清除之前的消息，避免显示其他模块的对话记录
  chatStore.clearMessages()
  chatStore.currentChatId = null
  chatStore.currentSession = null
  chatStore.fetchSessions({ app_type: 'love_app' })
})

// Auto-scroll when messages change or streaming updates
watch(
  () => [chatStore.messages.length, chatStore.streamingContent, chatStore.thinkingContent],
  () => {
    nextTick(scrollToBottom)
  }
)

// ---- Session Management ----
function selectSession(session) {
  chatStore.setCurrentSession(session)
  chatStore.fetchMessages(session.chat_id)
  panelOpen.value = false
}

async function handleDelete(session) {
  await chatStore.deleteSession(session.chat_id)
}

function onSessionCreated(session) {
  chatStore.fetchMessages(session.chat_id)
}

// ---- Messaging ----
function sendMessage() {
  const text = inputText.value.trim()
  if (!text || chatStore.streaming) return
  inputText.value = ''
  resetTextareaHeight()
  chatStore.sendMessage(text)
}

function useStarter(text) {
  inputText.value = text
  nextTick(() => {
    sendMessage()
  })
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// ---- Textarea auto-resize ----
function autoResize() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

function resetTextareaHeight() {
  const el = inputRef.value
  if (el) {
    el.style.height = 'auto'
  }
}

// ---- Scroll ----
function scrollToBottom() {
  const el = messagesRef.value
  if (el) {
    el.scrollTop = el.scrollHeight
  }
}

// ---- Metadata helpers ----
function getMeta(msg) {
  const meta = msg.metadata
  if (!meta) return {}
  if (typeof meta === 'string') {
    try { return JSON.parse(meta) } catch { return {} }
  }
  return meta
}

function hasRagSources(msg) {
  const sources = getMeta(msg).rag_sources
  return Array.isArray(sources) && sources.length > 0
}

function getRagSources(msg) {
  return getMeta(msg).rag_sources || []
}

function getSourceTitle(src, index) {
  return src.title || src.document_title || `来源 ${index + 1}`
}

function toggleMetadata(msg) {
  msg._metaOpen = !msg._metaOpen
}

// ---- Time formatting ----
function formatTime(time) {
  if (!time) return ''
  const d = new Date(time)
  if (isNaN(d.getTime())) return ''
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

function formatRelativeTime(time) {
  if (!time) return ''
  const d = new Date(time)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const diff = now - d
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return `${d.getMonth() + 1}/${d.getDate()}`
}
</script>

<style scoped>
.love-master {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

/* ---- Header ---- */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-5);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.btn-back {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius);
  color: var(--color-ink-muted);
  transition: all var(--duration-fast);
}

.btn-back:hover {
  background: var(--color-surface-hover);
  color: var(--color-ink);
}

.btn-back svg {
  width: 18px;
  height: 18px;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.page-title {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
  line-height: var(--leading-tight);
}

.page-subtitle {
  font-size: var(--text-xs);
  color: var(--color-ink-muted);
}

.header-status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-success);
}

.status-dot {
  width: 6px;
  height: 6px;
  background: var(--color-success);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

/* ---- Chat Container ---- */
.chat-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* ---- Session Panel ---- */
.session-panel {
  width: var(--sidebar-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-4);
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

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2);
}

.session-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3);
  border-radius: var(--border-radius);
  text-align: left;
  transition: all var(--duration-fast);
  position: relative;
}

.session-item:hover {
  background: var(--color-surface-hover);
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
  background: linear-gradient(135deg, #fdf2f8, #fce7f3);
  color: #ec4899;
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  flex-shrink: 0;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-ink-faint);
  margin-top: 2px;
}

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

.session-item:hover .session-delete {
  opacity: 1;
}

.session-delete:hover {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.session-delete svg {
  width: 14px;
  height: 14px;
}

.panel-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-6);
  color: var(--color-ink-muted);
}

.empty-icon {
  font-size: 32px;
  color: var(--color-accent-light);
  opacity: 0.5;
}

.panel-empty p {
  font-size: var(--text-sm);
}

.btn-create {
  padding: var(--space-2) var(--space-4);
  background: var(--color-accent);
  color: white;
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  transition: all var(--duration-fast);
}

.btn-create:hover {
  background: var(--color-accent-dark);
}

/* ---- Chat Main ---- */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--color-bg);
}

/* ---- No Session Selected ---- */
.no-session {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
}

.no-session-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent-bg);
  color: var(--color-accent);
  border-radius: 50%;
  opacity: 0.6;
}

.no-session-icon svg {
  width: 28px;
  height: 28px;
}

.no-session h3 {
  font-size: var(--text-lg);
  font-weight: var(--weight-medium);
  color: var(--color-ink);
}

.no-session p {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
}

/* ---- Welcome (empty chat) ---- */
.welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-5);
  padding: var(--space-8);
}

.welcome-avatar {
  margin-bottom: var(--space-2);
}

.avatar-large {
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-dark));
  color: white;
  font-size: 28px;
  border-radius: 50%;
  box-shadow: var(--glow-accent);
}

.welcome h3 {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
}

.welcome-desc {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  text-align: center;
  max-width: 360px;
  line-height: var(--leading-relaxed);
}

.starters {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  justify-content: center;
  margin-top: var(--space-2);
  max-width: 500px;
}

.starter-chip {
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-full);
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  transition: all var(--duration-fast);
}

.starter-chip:hover {
  border-color: var(--color-accent);
  color: var(--color-accent-dark);
  background: var(--color-accent-bg);
}

/* ---- Messages Area ---- */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6) var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* ---- Message Row ---- */
.message-row {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  animation: msgIn var(--duration-normal) var(--ease-out);
}

@keyframes msgIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* User messages — right aligned */
.user-row {
  justify-content: flex-end;
}

/* Assistant messages — left aligned */
.assistant-row {
  justify-content: flex-start;
}

/* ---- Avatar ---- */
.avatar-sm {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-dark));
  color: white;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* ---- Bubbles ---- */
.bubble {
  max-width: 70%;
  position: relative;
}

.user-bubble {
  background: var(--color-primary);
  color: white;
  border-radius: var(--border-radius-lg) var(--border-radius-lg) 4px var(--border-radius-lg);
  padding: var(--space-3) var(--space-4);
}

.assistant-bubble {
  background: var(--color-surface);
  color: var(--color-ink);
  border-radius: var(--border-radius-lg) var(--border-radius-lg) var(--border-radius-lg) 4px;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border-light);
}

.bubble-text {
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  white-space: pre-wrap;
  word-break: break-word;
}

.bubble-time {
  font-size: var(--text-xs);
  color: var(--color-ink-faint);
  margin-top: var(--space-1);
  text-align: right;
}

.user-bubble .bubble-time {
  color: rgba(255, 255, 255, 0.5);
}

/* ---- Thinking Indicator ---- */
.thinking-bubble {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-5);
}

.thinking-dots {
  display: flex;
  gap: 4px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-accent);
  animation: dotPulse 1.4s infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dotPulse {
  0%, 80%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1);
  }
}

.thinking-text {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
}

/* ---- Streaming Cursor ---- */
.streaming-text {
  position: relative;
}

.cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--color-accent);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* ---- Metadata ---- */
.metadata-area {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border-light);
}

.metadata-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-ink-muted);
  padding: var(--space-1) 0;
  transition: color var(--duration-fast);
}

.metadata-toggle:hover {
  color: var(--color-accent);
}

.metadata-toggle.expanded {
  color: var(--color-accent);
}

.meta-icon {
  width: 14px;
  height: 14px;
  transition: transform var(--duration-fast);
}

.metadata-toggle.expanded .meta-icon {
  transform: rotate(180deg);
}

.metadata-detail {
  margin-top: var(--space-3);
  padding: var(--space-3);
  background: var(--color-bg);
  border-radius: var(--border-radius);
  animation: slideDown var(--duration-normal) var(--ease-out);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.meta-section {
  margin-bottom: var(--space-2);
}

.meta-label {
  font-size: var(--text-xs);
  color: var(--color-ink-muted);
  font-weight: var(--weight-medium);
  display: block;
  margin-bottom: var(--space-1);
}

.meta-source {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-1) 0;
  font-size: var(--text-xs);
}

.source-name {
  color: var(--color-ink-light);
}

.source-score {
  color: var(--color-accent);
  font-weight: var(--weight-medium);
}

.meta-footer {
  display: flex;
  gap: var(--space-4);
  font-size: 11px;
  color: var(--color-ink-faint);
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border-light);
}

/* ---- Input Area ---- */
.input-area {
  padding: var(--space-4) var(--space-6) var(--space-5);
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-lg);
  padding: var(--space-2) var(--space-3);
  transition: border-color var(--duration-fast), box-shadow var(--duration-fast);
}

.input-wrapper:focus-within {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-bg);
}

.chat-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: var(--space-2);
  font-size: var(--text-base);
  resize: none;
  min-height: 24px;
  max-height: 120px;
  line-height: var(--leading-normal);
  color: var(--color-ink);
}

.chat-input::placeholder {
  color: var(--color-ink-faint);
}

.chat-input:disabled {
  opacity: 0.5;
}

.input-actions {
  display: flex;
  align-items: flex-end;
  flex-shrink: 0;
  padding-bottom: 2px;
}

.btn-send {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent);
  color: white;
  transition: all var(--duration-fast);
}

.btn-send:hover:not(:disabled) {
  background: var(--color-accent-dark);
  transform: scale(1.05);
  box-shadow: var(--glow-accent);
}

.btn-send:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.btn-send svg {
  width: 18px;
  height: 18px;
}

.btn-stop {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-danger-bg);
  color: var(--color-danger);
  border-radius: var(--border-radius-full);
  font-size: var(--text-sm);
  transition: all var(--duration-fast);
}

.btn-stop:hover {
  background: var(--color-danger);
  color: white;
}

.btn-stop svg {
  width: 14px;
  height: 14px;
}

.input-hint {
  text-align: center;
  margin-top: var(--space-2);
  font-size: 11px;
  color: var(--color-ink-faint);
}

.hint-streaming {
  color: var(--color-accent);
  animation: fadeInOut 2s infinite;
}

@keyframes fadeInOut {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

/* ---- Animations ---- */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* ---- Responsive ---- */
@media (max-width: 768px) {
  .btn-toggle-panel {
    display: flex;
  }

  .session-panel {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 280px;
    z-index: var(--z-sticky);
    transform: translateX(-100%);
    transition: transform var(--duration-slow) var(--ease-out);
  }

  .session-panel.open {
    transform: translateX(0);
  }

  .panel-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: calc(var(--z-sticky) - 1);
  }

  .chat-container {
    position: relative;
  }

  .messages-area {
    padding: var(--space-4);
  }

  .input-area {
    padding: var(--space-3) var(--space-4) var(--space-4);
  }

  .bubble {
    max-width: 85%;
  }

  .starters {
    flex-direction: column;
    align-items: stretch;
  }

  .welcome {
    padding: var(--space-6) var(--space-4);
  }
}

.btn-toggle-panel {
  display: none;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius);
  color: var(--color-ink-muted);
  transition: all var(--duration-fast);
}

.btn-toggle-panel:hover {
  background: var(--color-surface-hover);
  color: var(--color-ink);
}

.btn-toggle-panel svg {
  width: 18px;
  height: 18px;
}
</style>
