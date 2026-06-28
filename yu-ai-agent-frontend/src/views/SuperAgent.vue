<template>
  <div class="super-agent">
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
          <h1 class="page-title">超级智能体</h1>
          <p class="page-subtitle">自主规划，多步推理</p>
        </div>
      </div>
      <div class="header-status">
        <span class="status-dot" />
        <span>就绪</span>
      </div>
    </header>

    <div class="agent-container">
      <!-- Mobile Overlay -->
      <div v-if="panelOpen" class="panel-overlay" @click="panelOpen = false" />

      <!-- Session Panel -->
      <aside class="session-panel" :class="{ open: panelOpen }">
        <div class="panel-header">
          <h2 class="panel-title">任务列表</h2>
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
            <div class="session-icon">◈</div>
            <div class="session-info">
              <span class="session-title">{{ session.title || '新任务' }}</span>
              <span class="session-time">{{ formatRelativeTime(session.createTime) }}</span>
            </div>
            <button
              class="session-delete"
              @click.stop="handleDelete(session)"
              title="删除任务"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
              </svg>
            </button>
          </button>
        </div>

        <div class="panel-empty" v-else>
          <div class="empty-icon">◈</div>
          <p>还没有任务</p>
          <button class="btn-create" @click="showCreateDialog = true">开始新任务</button>
        </div>
      </aside>

      <!-- Main Task Area -->
      <main class="task-main">
        <!-- No session selected -->
        <div v-if="!chatStore.currentChatId" class="no-session">
          <div class="no-session-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <h3>选择一个任务</h3>
          <p>从左侧选择已有任务，或创建新的对话</p>
        </div>

        <template v-else>
          <!-- Task input -->
          <div class="task-input-area">
            <textarea
              v-model="taskInput"
              class="task-textarea"
              placeholder="描述你想要完成的任务，越详细越好..."
              rows="3"
              :disabled="running"
              @keydown.enter.ctrl.exact="submitTask"
            />
            <div class="task-actions">
              <button
                class="btn-run"
                :disabled="!taskInput.trim() || running"
                @click="submitTask"
              >
                <svg v-if="!running" class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="5 3 19 12 5 21 5 3" fill="currentColor" />
                </svg>
                <span v-if="!running">开始执行</span>
                <span v-else class="running-label">
                  <span class="running-dot" />
                  执行中...
                </span>
              </button>
              <button
                v-if="running"
                class="btn-cancel"
                @click="cancelTask"
              >
                取消任务
              </button>
            </div>
            <div class="task-hint">Ctrl + Enter 快速提交</div>
          </div>

          <!-- Task status panel -->
          <div v-if="currentTask" class="task-panel" :class="currentTask.status">
            <!-- Status header -->
            <div class="task-status-header">
              <div class="status-badge" :class="currentTask.status">
                <span class="status-dot" />
                <span class="status-text">{{ statusLabel }}</span>
              </div>
              <span class="task-time">{{ formatTime(currentTask.createTime) }}</span>
            </div>

            <!-- Pending state -->
            <div v-if="currentTask.status === 'pending'" class="state-pending">
              <div class="pending-animation">
                <div class="pending-ring" />
                <div class="pending-ring delay-1" />
                <div class="pending-ring delay-2" />
              </div>
              <p class="state-desc">正在排队等待执行资源...</p>
            </div>

            <!-- Running state -->
            <div v-if="currentTask.status === 'running'" class="state-running">
              <div class="running-visual">
                <div class="running-spinner">
                  <svg viewBox="0 0 50 50" class="spinner-svg">
                    <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="80 40" stroke-linecap="round" />
                  </svg>
                </div>
                <div class="running-info">
                  <p class="running-title">智能体正在执行任务</p>
                  <p class="running-elapsed">已耗时 {{ elapsedTime }}</p>
                </div>
              </div>
              <div class="running-steps-hint">
                <span class="hint-dot" />
                <span>正在调用工具和推理，请耐心等待</span>
              </div>
            </div>

            <!-- Steps list (shown when completed) -->
            <div v-if="stepsList.length > 0" class="steps-section">
              <h4 class="section-title">执行步骤</h4>
              <div class="steps-timeline">
                <div
                  v-for="(step, i) in stepsList"
                  :key="i"
                  class="step-item"
                  :class="step.status || 'success'"
                >
                  <div class="step-marker">
                    <span class="step-num">{{ i + 1 }}</span>
                  </div>
                  <div class="step-body">
                    <div class="step-header">
                      <span class="step-action">{{ formatAction(step.action) }}</span>
                      <span v-if="step.duration_ms" class="step-duration">{{ formatDuration(step.duration_ms) }}</span>
                    </div>
                    <div v-if="step.thought" class="step-thought">
                      <span class="thought-label">思考</span>
                      <span class="thought-text">{{ step.thought }}</span>
                    </div>
                    <div v-if="step.detail || step.observation" class="step-detail">
                      {{ step.detail || step.observation }}
                    </div>
                    <div v-if="step.error" class="step-error">
                      {{ step.error }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Final result -->
            <div v-if="currentTask.result && ['completed', 'failed'].includes(currentTask.status)" class="result-section">
              <h4 class="section-title">
                {{ currentTask.status === 'completed' ? '执行结果' : '错误信息' }}
              </h4>
              <div class="result-content" :class="{ 'result-error': currentTask.status === 'failed' }">
                <MarkdownRenderer v-if="currentTask.status === 'completed'" :content="currentTask.result" />
                <template v-else>{{ currentTask.result }}</template>
              </div>
            </div>

            <!-- Cancelled state -->
            <div v-if="currentTask.status === 'cancelled'" class="state-cancelled">
              <p>任务已取消</p>
            </div>
          </div>

          <!-- Message history -->
          <div v-if="!currentTask && chatStore.messages.length > 0" class="messages-panel">
            <h4 class="section-title">对话记录</h4>
            <div class="msg-list">
              <div
                v-for="msg in chatStore.messages"
                :key="msg.id"
                class="msg-item"
                :class="msg.role"
              >
                <div class="msg-role">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
                <div class="msg-content">
                  <MarkdownRenderer v-if="msg.role === 'assistant'" :content="msg.content" />
                  <template v-else>{{ msg.content }}</template>
                </div>
                <div class="msg-time">{{ formatTime(msg.createTime) }}</div>
              </div>
            </div>
          </div>

          <!-- Empty state (no task yet) -->
          <div v-else-if="!currentTask && !running" class="empty-state">
            <div class="empty-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            <h3>描述你的任务</h3>
            <p>在上方输入框中描述你想完成的任务，智能体会自动规划并执行</p>
            <div class="example-tasks">
              <button
                v-for="ex in examples"
                :key="ex"
                class="example-chip"
                @click="taskInput = ex"
              >
                {{ ex }}
              </button>
            </div>
          </div>
        </template>
      </main>
    </div>

    <!-- Create Session Dialog -->
    <CreateSessionDialog
      :visible="showCreateDialog"
      default-type="manus"
      @close="showCreateDialog = false"
      @created="onSessionCreated"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import request from '@/utils/request'
import CreateSessionDialog from '@/components/CreateSessionDialog.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

const chatStore = useChatStore()
const taskInput = ref('')
const currentTask = ref(null)
const running = ref(false)
const showCreateDialog = ref(false)
const elapsedSeconds = ref(0)
const panelOpen = ref(false)
let pollTimer = null
let elapsedTimer = null

const examples = [
  '帮我搜索最新的 AI 技术趋势并整理成报告',
  '分析这段代码的性能问题并给出优化建议',
  '帮我写一份产品需求文档的提纲'
]

// ---- Computed ----
const statusLabel = computed(() => {
  const map = {
    pending: '等待中',
    running: '执行中',
    completed: '已完成',
    failed: '执行失败',
    cancelled: '已取消'
  }
  return map[currentTask.value?.status] || ''
})

const stepsList = computed(() => {
  return currentTask.value?.steps || []
})

const elapsedTime = computed(() => {
  const s = elapsedSeconds.value
  if (s < 60) return `${s}秒`
  const m = Math.floor(s / 60)
  const rem = s % 60
  return `${m}分${rem}秒`
})

// ---- Lifecycle ----
onMounted(() => {
  // 清除之前的消息，避免显示其他模块的对话记录
  chatStore.clearMessages()
  chatStore.currentChatId = null
  chatStore.currentSession = null
  chatStore.fetchSessions({ app_type: 'manus' })
})

onUnmounted(() => {
  stopPolling()
  stopElapsed()
})

// ---- Session Management ----
function selectSession(session) {
  chatStore.setCurrentSession(session)
  chatStore.fetchMessages(session.chat_id)
  currentTask.value = null
  stopPolling()
  stopElapsed()
  panelOpen.value = false
}

async function handleDelete(session) {
  await chatStore.deleteSession(session.chat_id)
  if (session.chat_id === chatStore.currentChatId) {
    currentTask.value = null
    stopPolling()
    stopElapsed()
  }
}

function onSessionCreated(session) {
  currentTask.value = null
  stopPolling()
  stopElapsed()
}

// ---- Task submission ----
async function submitTask() {
  const text = taskInput.value.trim()
  if (!text || running.value) return

  running.value = true
  elapsedSeconds.value = 0
  startElapsed()

  try {
    const res = await request({
      url: '/v1/agent/run',
      method: 'post',
      data: {
        message: text,
        chat_id: chatStore.currentChatId
      }
    })
    const task = res.data || res
    currentTask.value = { ...task, steps: task.steps || [] }
    startPolling(task.taskId || task.task_id)
  } catch {
    running.value = false
    stopElapsed()
  }
}

// ---- Polling ----
function startPolling(taskId) {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const res = await request({
        url: `/v1/agent/status/${taskId}`,
        method: 'get'
      })
      const task = res.data || res
      currentTask.value = task

      if (['completed', 'failed', 'cancelled'].includes(task.status)) {
        stopPolling()
        stopElapsed()
        running.value = false
      }
    } catch {
      stopPolling()
      stopElapsed()
      running.value = false
    }
  }, 3000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// ---- Elapsed timer ----
function startElapsed() {
  stopElapsed()
  elapsedTimer = setInterval(() => {
    elapsedSeconds.value++
  }, 1000)
}

function stopElapsed() {
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
    elapsedTimer = null
  }
}

// ---- Cancel ----
async function cancelTask() {
  if (!currentTask.value) return
  const taskId = currentTask.value.taskId || currentTask.value.task_id
  try {
    await request({
      url: `/v1/agent/cancel/${taskId}`,
      method: 'post'
    })
    currentTask.value.status = 'cancelled'
    currentTask.value.result = '用户取消任务'
    stopPolling()
    stopElapsed()
    running.value = false
  } catch {}
}

// ---- Formatters ----
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

function formatAction(action) {
  if (!action) return '执行'
  const map = {
    rag_retrieve: '知识库检索',
    llm_call: 'LLM 推理',
    web_search: '网络搜索',
    file_operation: '文件操作',
    knowledge_search: '知识搜索',
    calculator: '计算',
    web_fetch: '网页抓取'
  }
  return map[action] || action
}

function formatDuration(ms) {
  if (!ms) return ''
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(1)}s`
}
</script>

<style scoped>
.super-agent {
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

/* ---- Container ---- */
.agent-container {
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
  background: rgba(59, 130, 246, 0.08);
}

.session-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  color: #3b82f6;
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
  color: #93c5fd;
  opacity: 0.5;
}

.panel-empty p {
  font-size: var(--text-sm);
}

.btn-create {
  padding: var(--space-2) var(--space-4);
  background: var(--color-primary);
  color: white;
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  transition: all var(--duration-fast);
}

.btn-create:hover {
  background: var(--color-primary-light);
}

/* ---- Task Main ---- */
.task-main {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* ---- No Session ---- */
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
  background: rgba(59, 130, 246, 0.08);
  color: #3b82f6;
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

/* ---- Task Input ---- */
.task-input-area {
  background: var(--color-surface);
  border-radius: var(--border-radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
}

.task-textarea {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-base);
  resize: vertical;
  min-height: 80px;
  transition: border-color var(--duration-fast);
  line-height: var(--leading-normal);
  color: var(--color-ink);
  background: var(--color-bg);
}

.task-textarea::placeholder {
  color: var(--color-ink-faint);
}

.task-textarea:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.task-textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.task-actions {
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-4);
  align-items: center;
}

.btn-run {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  background: var(--color-primary);
  color: white;
  border-radius: var(--border-radius);
  font-weight: var(--weight-medium);
  font-size: var(--text-sm);
  transition: all var(--duration-fast);
}

.btn-run:hover:not(:disabled) {
  background: var(--color-primary-light);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-run:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-icon {
  width: 16px;
  height: 16px;
}

.running-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.running-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: white;
  animation: pulse 1.2s infinite;
}

.btn-cancel {
  padding: var(--space-3) var(--space-5);
  background: var(--color-surface-hover);
  color: var(--color-ink-muted);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  transition: all var(--duration-fast);
}

.btn-cancel:hover {
  background: var(--color-danger-bg);
  color: var(--color-danger);
  border-color: var(--color-danger);
}

.task-hint {
  margin-top: var(--space-2);
  font-size: 11px;
  color: var(--color-ink-faint);
}

/* ---- Task Panel ---- */
.task-panel {
  background: var(--color-surface);
  border-radius: var(--border-radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  animation: fadeSlideIn var(--duration-normal) var(--ease-out);
}

@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Status header */
.task-status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-5);
}

.status-badge {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--border-radius-full);
}

.status-badge.pending {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.status-badge.running {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.status-badge.completed {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.status-badge.failed {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.status-badge.cancelled {
  background: var(--color-surface-hover);
  color: var(--color-ink-muted);
}

.status-badge .status-dot {
  width: 6px;
  height: 6px;
  background: currentColor;
  border-radius: 50%;
}

.status-badge.running .status-dot {
  animation: pulse 1.2s infinite;
}

.task-time {
  font-size: var(--text-xs);
  color: var(--color-ink-faint);
}

/* ===== Pending State ===== */
.state-pending {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-8) 0;
}

.pending-animation {
  position: relative;
  width: 48px;
  height: 48px;
}

.pending-ring {
  position: absolute;
  inset: 0;
  border: 2px solid rgba(59, 130, 246, 0.2);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1.5s linear infinite;
}

.pending-ring.delay-1 {
  inset: 6px;
  animation-delay: 0.3s;
  border-top-color: #60a5fa;
}

.pending-ring.delay-2 {
  inset: 12px;
  animation-delay: 0.6s;
  border-top-color: #3b82f6;
  opacity: 0.6;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.state-desc {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
}

/* ===== Running State ===== */
.state-running {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4) 0;
}

.running-visual {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.running-spinner {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.spinner-svg {
  width: 100%;
  height: 100%;
  color: #3b82f6;
  animation: spin 1s linear infinite;
}

.running-info {
  flex: 1;
}

.running-title {
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--color-ink);
}

.running-elapsed {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  margin-top: var(--space-1);
}

.running-steps-hint {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: rgba(59, 130, 246, 0.06);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  color: #3b82f6;
}

.hint-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3b82f6;
  animation: pulse 1.5s infinite;
  flex-shrink: 0;
}

/* ===== Steps Timeline ===== */
.steps-section {
  margin-top: var(--space-5);
  padding-top: var(--space-5);
  border-top: 1px solid var(--color-border-light);
}

.section-title {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--color-ink-muted);
  margin-bottom: var(--space-4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.steps-timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
  position: relative;
}

.step-item {
  display: flex;
  gap: var(--space-4);
  position: relative;
  padding-bottom: var(--space-5);
}

.step-item:last-child {
  padding-bottom: 0;
}

/* Timeline line */
.step-item:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 15px;
  top: 32px;
  bottom: 0;
  width: 2px;
  background: var(--color-border-light);
}

.step-marker {
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.step-num {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.08);
  color: #3b82f6;
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
}

.step-item.success .step-num {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.step-item.failed .step-num {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.step-body {
  flex: 1;
  min-width: 0;
  padding-top: 4px;
}

.step-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.step-action {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
}

.step-duration {
  font-size: 11px;
  color: var(--color-ink-faint);
  padding: 1px 6px;
  background: var(--color-surface-hover);
  border-radius: var(--border-radius-full);
}

.step-thought {
  margin-top: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg);
  border-radius: var(--border-radius);
  border-left: 3px solid #93c5fd;
}

.thought-label {
  font-size: 11px;
  color: #3b82f6;
  font-weight: var(--weight-medium);
  display: block;
  margin-bottom: 2px;
}

.thought-text {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  line-height: var(--leading-relaxed);
}

.step-detail {
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  line-height: var(--leading-relaxed);
}

.step-error {
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-danger);
  padding: var(--space-2) var(--space-3);
  background: var(--color-danger-bg);
  border-radius: var(--border-radius);
}

/* ===== Result ===== */
.result-section {
  margin-top: var(--space-5);
  padding-top: var(--space-5);
  border-top: 1px solid var(--color-border-light);
}

.result-content {
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  color: var(--color-ink);
  white-space: pre-wrap;
  word-break: break-word;
  padding: var(--space-4);
  background: var(--color-bg);
  border-radius: var(--border-radius);
  border: 1px solid var(--color-border-light);
}

.result-content.result-error {
  background: var(--color-danger-bg);
  color: var(--color-danger);
  border-color: var(--color-danger);
}

/* ===== Cancelled ===== */
.state-cancelled {
  padding: var(--space-6) 0;
  text-align: center;
  color: var(--color-ink-muted);
  font-size: var(--text-sm);
}

/* ===== Messages Panel ===== */
.messages-panel {
  background: var(--color-surface);
  border-radius: var(--border-radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
}

.msg-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.msg-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.msg-item.user {
  align-items: flex-end;
}

.msg-item.assistant {
  align-items: flex-start;
}

.msg-role {
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-ink-muted);
}

.msg-content {
  max-width: 80%;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--border-radius-lg);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  white-space: pre-wrap;
  word-break: break-word;
}

.msg-item.user .msg-content {
  background: var(--color-primary);
  color: white;
  border-bottom-right-radius: var(--space-1);
}

.msg-item.assistant .msg-content {
  background: var(--color-bg);
  color: var(--color-ink);
  border-bottom-left-radius: var(--space-1);
  border: 1px solid var(--color-border-light);
}

.msg-time {
  font-size: 11px;
  color: var(--color-ink-faint);
}

/* ===== Empty State ===== */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  color: var(--color-ink-muted);
  padding: var(--space-8);
}

.empty-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(59, 130, 246, 0.06);
  color: #93c5fd;
  border-radius: 50%;
  opacity: 0.5;
}

.empty-icon svg {
  width: 28px;
  height: 28px;
}

.empty-state h3 {
  font-size: var(--text-lg);
  font-weight: var(--weight-medium);
  color: var(--color-ink);
}

.empty-state p {
  font-size: var(--text-sm);
  text-align: center;
  max-width: 400px;
  line-height: var(--leading-relaxed);
}

.example-tasks {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  justify-content: center;
  margin-top: var(--space-3);
  max-width: 500px;
}

.example-chip {
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-full);
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  transition: all var(--duration-fast);
}

.example-chip:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.04);
}

/* ===== Animations ===== */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ===== Responsive ===== */
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

  .agent-container {
    position: relative;
  }

  .task-main {
    padding: var(--space-4);
  }

  .example-tasks {
    flex-direction: column;
    align-items: stretch;
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
