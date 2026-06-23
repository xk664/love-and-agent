<template>
  <div class="love-master">
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-dot coral" />
        恋爱大师
      </h1>
      <p class="page-subtitle">用温暖的方式，理解你的每一种心情</p>
    </div>

    <div class="chat-container">
      <!-- Session Panel -->
      <SessionPanel
        :sessions="chatStore.sessions"
        :active-id="chatStore.currentChatId"
        accent="coral"
        app-type="love_app"
        empty-icon="♡"
        empty-text="还没有对话，点击「新建对话」开始吧"
        @create="showCreateDialog = true"
        @select="selectSession"
        @delete="handleDelete"
      />

      <!-- Chat area -->
      <div class="chat-main">
        <!-- No session selected -->
        <div v-if="!chatStore.currentChatId" class="no-session">
          <div class="no-session-icon">♡</div>
          <h3>选择一个对话</h3>
          <p>从左侧选择已有对话，或创建新的对话</p>
        </div>

        <!-- Active chat -->
        <template v-else>
          <!-- Messages area -->
          <div class="messages-area" ref="messagesRef" @scroll="onMessagesScroll">
            <!-- Welcome (empty chat) -->
            <div v-if="displayMessages.length === 0 && !chatStore.streaming" class="welcome">
              <div class="welcome-avatar">
                <span class="avatar-circle">♡</span>
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
                </div>
              </div>

              <!-- Assistant message -->
              <div v-else class="message-row assistant-row">
                <div class="avatar-sm">♡</div>
                <div class="bubble assistant-bubble">
                  <div class="bubble-text">{{ msg.content }}</div>

                  <!-- Metadata toggle -->
                  <div v-if="hasMetadata(msg)" class="metadata-area">
                    <button
                      class="metadata-toggle"
                      :class="{ expanded: msg._metaOpen }"
                      @click="toggleMetadata(msg)"
                    >
                      <span class="meta-icon">◎</span>
                      <span>{{ msg._metaOpen ? '收起详情' : '查看来源' }}</span>
                    </button>
                    <div v-if="msg._metaOpen" class="metadata-detail">
                      <div v-if="getRagSources(msg).length" class="meta-section">
                        <span class="meta-label">参考来源</span>
                        <div
                          v-for="(src, i) in getRagSources(msg)"
                          :key="i"
                          class="meta-source"
                        >
                          <span class="source-name">{{ src.title || src.document_title || `来源 ${i + 1}` }}</span>
                          <span v-if="src.score" class="source-score">{{ (src.score * 100).toFixed(0) }}%</span>
                        </div>
                      </div>
                      <div class="meta-footer">
                        <span v-if="getModel(msg)">模型: {{ getModel(msg) }}</span>
                        <span v-if="getTokens(msg)">Token: {{ getTokens(msg) }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Timestamp -->
                  <div class="bubble-time">{{ formatTime(msg.createTime) }}</div>
                </div>
              </div>
            </template>

            <!-- Thinking indicator -->
            <div v-if="chatStore.thinkingContent" class="message-row assistant-row">
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
                  {{ chatStore.streamingContent }}<span class="cursor" />
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
                  <span class="stop-icon" />
                  停止
                </button>
                <button
                  v-else
                  class="btn-send coral"
                  :disabled="!inputText.trim()"
                  @click="sendMessage"
                >
                  <svg class="send-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
      </div>
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
import SessionPanel from '@/components/SessionPanel.vue'
import CreateSessionDialog from '@/components/CreateSessionDialog.vue'

const chatStore = useChatStore()
const inputText = ref('')
const showCreateDialog = ref(false)
const messagesRef = ref(null)
const inputRef = ref(null)
let messageKeyCounter = 0

// Suggested conversation starters
const starters = [
  '最近感情不太顺利，想聊聊',
  '怎么判断一个人是不是喜欢我',
  '异地恋好难，有什么建议吗',
  '刚分手，不知道该怎么办'
]

// ---- Computed: messages with stable keys ----
const displayMessages = computed(() => {
  return chatStore.messages.map((msg) => ({
    ...msg,
    _key: msg.id || msg.createTime || ++messageKeyCounter,
    _metaOpen: msg._metaOpen || false
  }))
})

// ---- Lifecycle ----
onMounted(() => {
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
  const id = session.chatId || session.chat_id
  chatStore.fetchMessages(id)
}

async function handleDelete(session) {
  const id = session.chatId || session.chat_id
  await chatStore.deleteSession(id)
}

function onSessionCreated(session) {
  const id = session.chatId || session.chat_id
  chatStore.fetchMessages(id)
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

function onMessagesScroll() {
  // Could implement "load more" for history pagination here
}

// ---- Metadata helpers ----
function hasMetadata(msg) {
  const meta = msg.metadata
  if (!meta) return false
  if (typeof meta === 'string') {
    try {
      const parsed = JSON.parse(meta)
      return parsed.rag_sources?.length > 0 || parsed.tokens_used || parsed.model
    } catch {
      return false
    }
  }
  return meta.rag_sources?.length > 0 || meta.tokens_used || meta.model
}

function getMeta(msg) {
  const meta = msg.metadata
  if (!meta) return {}
  if (typeof meta === 'string') {
    try { return JSON.parse(meta) } catch { return {} }
  }
  return meta
}

function getRagSources(msg) {
  return getMeta(msg).rag_sources || []
}

function getModel(msg) {
  return getMeta(msg).model
}

function getTokens(msg) {
  return getMeta(msg).tokens_used
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
</script>

<style scoped>
.love-master {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-mist);
}

.page-header {
  padding: var(--space-5) var(--space-6);
  background: var(--color-cloud);
  border-bottom: 1px solid var(--color-stone-bg);
  flex-shrink: 0;
}

.page-title {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.title-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.title-dot.coral {
  background: var(--color-coral);
  box-shadow: var(--shadow-glow-coral);
}

.page-subtitle {
  font-size: var(--text-sm);
  color: var(--color-stone);
  margin-top: var(--space-1);
}

/* ===== Chat Container ===== */
.chat-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--color-mist);
}

/* ===== No Session Selected ===== */
.no-session {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  color: var(--color-stone);
}

.no-session-icon {
  font-size: 48px;
  color: var(--color-coral-light);
  opacity: 0.6;
}

.no-session h3 {
  font-size: var(--text-lg);
  font-weight: var(--weight-medium);
  color: var(--color-ink-muted);
}

.no-session p {
  font-size: var(--text-sm);
}

/* ===== Welcome (empty chat) ===== */
.welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-8);
}

.welcome-avatar {
  margin-bottom: var(--space-2);
}

.avatar-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-coral), var(--color-coral-light));
  color: white;
  font-size: 28px;
  box-shadow: var(--shadow-glow-coral);
}

.welcome h3 {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
}

.welcome-desc {
  font-size: var(--text-sm);
  color: var(--color-stone);
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
  max-width: 480px;
}

.starter-chip {
  padding: var(--space-2) var(--space-4);
  background: var(--color-cloud);
  border: 1px solid var(--color-stone-light);
  border-radius: var(--border-radius-full);
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  transition: all var(--duration-fast);
  cursor: pointer;
}

.starter-chip:hover {
  border-color: var(--color-coral);
  color: var(--color-coral);
  background: var(--color-coral-bg);
}

/* ===== Messages Area ===== */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6) var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* ===== Message Row ===== */
.message-row {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  animation: msgIn var(--duration-normal) var(--ease-out);
}

@keyframes msgIn {
  from {
    opacity: 0;
    transform: translateY(6px);
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

/* ===== Avatar ===== */
.avatar-sm {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-coral), var(--color-coral-light));
  color: white;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}

/* ===== Bubbles ===== */
.bubble {
  max-width: 70%;
  position: relative;
}

.user-bubble {
  background: var(--color-coral);
  color: white;
  border-radius: var(--border-radius-lg) var(--border-radius-lg) 4px var(--border-radius-lg);
  padding: var(--space-3) var(--space-4);
}

.assistant-bubble {
  background: var(--color-cloud);
  color: var(--color-ink);
  border-radius: var(--border-radius-lg) var(--border-radius-lg) var(--border-radius-lg) 4px;
  padding: var(--space-3) var(--space-4);
  box-shadow: var(--shadow-sm);
}

.bubble-text {
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  white-space: pre-wrap;
  word-break: break-word;
}

.bubble-time {
  font-size: 11px;
  color: var(--color-stone-light);
  margin-top: var(--space-1);
  text-align: right;
}

.user-bubble .bubble-time {
  color: rgba(255, 255, 255, 0.6);
}

/* ===== Thinking Indicator ===== */
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
  background: var(--color-coral);
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
  color: var(--color-stone);
}

/* ===== Streaming Cursor ===== */
.streaming-text {
  position: relative;
}

.cursor {
  display: inline-block;
  width: 2px;
  height: 1.1em;
  background: var(--color-coral);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* ===== Metadata ===== */
.metadata-area {
  margin-top: var(--space-2);
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-stone-bg);
}

.metadata-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-stone);
  padding: var(--space-1) 0;
  transition: color var(--duration-fast);
}

.metadata-toggle:hover {
  color: var(--color-coral);
}

.metadata-toggle.expanded {
  color: var(--color-coral);
}

.meta-icon {
  font-size: 12px;
  transition: transform var(--duration-fast);
}

.metadata-toggle.expanded .meta-icon {
  transform: rotate(180deg);
}

.metadata-detail {
  margin-top: var(--space-2);
  padding: var(--space-3);
  background: var(--color-mist);
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
  color: var(--color-stone);
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
  color: var(--color-ink-muted);
}

.source-score {
  color: var(--color-coral);
  font-weight: var(--weight-medium);
}

.meta-footer {
  display: flex;
  gap: var(--space-4);
  font-size: 11px;
  color: var(--color-stone-light);
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-stone-bg);
}

/* ===== Input Area ===== */
.input-area {
  padding: var(--space-4) var(--space-8) var(--space-5);
  background: var(--color-cloud);
  border-top: 1px solid var(--color-stone-bg);
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  background: var(--color-mist);
  border: 1px solid var(--color-stone-light);
  border-radius: var(--border-radius-lg);
  padding: var(--space-2) var(--space-3);
  transition: border-color var(--duration-fast), box-shadow var(--duration-fast);
}

.input-wrapper:focus-within {
  border-color: var(--color-coral);
  box-shadow: 0 0 0 3px var(--color-coral-bg);
}

.chat-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: var(--space-2) var(--space-2);
  font-size: var(--text-base);
  resize: none;
  min-height: 24px;
  max-height: 120px;
  line-height: var(--leading-normal);
  font-family: var(--font-sans);
  color: var(--color-ink);
}

.chat-input::placeholder {
  color: var(--color-stone-light);
}

.chat-input:disabled {
  opacity: 0.6;
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
  transition: all var(--duration-fast);
}

.btn-send.coral {
  background: var(--color-coral);
  color: white;
}

.btn-send.coral:hover:not(:disabled) {
  background: #d45a78;
  transform: scale(1.05);
}

.btn-send:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.send-icon {
  width: 18px;
  height: 18px;
}

.btn-stop {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-stone-bg);
  color: var(--color-ink-muted);
  border-radius: var(--border-radius-full);
  font-size: var(--text-sm);
  transition: all var(--duration-fast);
}

.btn-stop:hover {
  background: var(--color-danger);
  color: white;
}

.stop-icon {
  width: 10px;
  height: 10px;
  background: currentColor;
  border-radius: 2px;
}

.input-hint {
  text-align: center;
  margin-top: var(--space-2);
  font-size: 11px;
  color: var(--color-stone-light);
}

.hint-streaming {
  color: var(--color-coral);
  animation: fadeInOut 2s infinite;
}

@keyframes fadeInOut {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
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
</style>
