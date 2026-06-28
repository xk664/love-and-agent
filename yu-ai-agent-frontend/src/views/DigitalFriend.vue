<template>
  <div class="digital-friend">
    <!-- Header -->
    <header class="page-header">
      <div class="header-left">
        <button class="btn-back" @click="$router.push('/')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <!-- Mobile: toggle friends panel -->
        <button class="btn-toggle-panel" @click="panelOpen = !panelOpen">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18M3 12h18M3 18h18" />
          </svg>
        </button>
        <div class="header-info">
          <h1 class="page-title">数字朋友</h1>
          <p class="page-subtitle">创建懂你的AI伙伴</p>
        </div>
      </div>
      <div class="header-status">
        <span class="status-dot" />
        <span>在线</span>
      </div>
    </header>

    <div class="main-container">
      <!-- Mobile Overlay -->
      <div v-if="panelOpen" class="panel-overlay" @click="panelOpen = false" />

      <!-- Friends Panel -->
      <aside class="friends-panel" :class="{ open: panelOpen }">
        <div class="panel-header">
          <h2 class="panel-title">朋友列表</h2>
          <button class="btn-new" @click="showCreateDialog = true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
            <span>新建</span>
          </button>
        </div>

        <div class="friends-list" v-if="friends.length > 0">
          <button
            v-for="friend in friends"
            :key="friend.friend_id"
            class="friend-item"
            :class="{ active: currentFriend?.friend_id === friend.friend_id }"
            @click="selectFriend(friend)"
          >
            <div class="friend-avatar" :style="{ background: getAvatarGradient(friend.friend_id) }">
              {{ friend.name.charAt(0) }}
            </div>
            <div class="friend-info">
              <span class="friend-name">{{ friend.name }}</span>
              <span class="friend-desc">{{ friend.description || '暂无描述' }}</span>
            </div>
            <button
              class="friend-delete"
              @click.stop="handleDeleteFriend(friend)"
              title="删除朋友"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
              </svg>
            </button>
          </button>
        </div>

        <div class="panel-empty" v-else>
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
          <p>还没有数字朋友</p>
          <button class="btn-create" @click="showCreateDialog = true">创建第一个朋友</button>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="content-main">
        <!-- No friend selected -->
        <div v-if="!currentFriend" class="no-friend">
          <div class="no-friend-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
          <h3>选择一个朋友</h3>
          <p>从左侧选择已有朋友，或创建新的数字朋友</p>
        </div>

        <!-- Friend selected -->
        <template v-else>
          <!-- Friend Header -->
          <div class="friend-header">
            <div class="header-avatar" :style="{ background: getAvatarGradient(currentFriend.friend_id) }">
              {{ currentFriend.name.charAt(0) }}
            </div>
            <div class="header-details">
              <h2 class="header-name">{{ currentFriend.name }}</h2>
              <p class="header-desc">{{ currentFriend.description || '这个人很神秘，什么都没留下' }}</p>
            </div>
            <div class="header-actions">
              <button class="btn-icon" @click="showMaterialDialog = true" title="管理素材">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
              </button>
              <button class="btn-icon" @click="showSettingsDialog = true" title="设置">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                </svg>
              </button>
              <button
                class="btn-distill"
                @click="handleDistill"
                :disabled="distillStatus === 'processing' || distillStatus === 'calibrating'"
              >
                <svg v-if="distillStatus !== 'processing'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                </svg>
                <span v-if="distillStatus === 'processing'" class="spinner" />
                <span v-if="distillStatus === 'calibrating'">已完成</span>
                <span v-else>{{ distillStatus === 'processing' ? '生成中...' : '生成人格' }}</span>
              </button>
            </div>
          </div>

          <!-- Messages Area -->
          <div class="messages-area" ref="messagesRef">
            <!-- Welcome -->
            <div v-if="messages.length === 0" class="welcome">
              <div class="welcome-avatar" :style="{ background: getAvatarGradient(currentFriend.friend_id) }">
                {{ currentFriend.name.charAt(0) }}
              </div>
              <h3>你好，我是{{ currentFriend.name }}</h3>
              <p class="welcome-desc">{{ currentFriend.description || '很高兴认识你，让我们开始聊天吧！' }}</p>
              <div class="welcome-hint">
                <p>💡 提示：在「管理素材」中添加关于这个朋友的资料，然后点击「生成人格」来训练AI</p>
              </div>
            </div>

            <!-- Message list -->
            <template v-for="msg in messages" :key="msg.id || msg._key">
              <!-- User message -->
              <div v-if="msg.role === 'user'" class="message-row user-row">
                <div class="bubble user-bubble">
                  <div class="bubble-text">{{ msg.content }}</div>
                  <div class="bubble-time">{{ formatTime(msg.createTime) }}</div>
                </div>
              </div>

              <!-- Assistant message -->
              <div v-else class="message-row assistant-row">
                <div class="avatar-sm" :style="{ background: getAvatarGradient(currentFriend.friend_id) }">
                  {{ currentFriend.name.charAt(0) }}
                </div>
                <div class="bubble assistant-bubble">
                  <div class="bubble-text">
                    <MarkdownRenderer :content="msg.content" />
                  </div>
                </div>
              </div>
            </template>

            <!-- Thinking indicator -->
            <div v-if="chatStore.streaming && !chatStore.streamingContent" class="message-row assistant-row">
              <div class="avatar-sm" :style="{ background: getAvatarGradient(currentFriend.friend_id) }">
                {{ currentFriend.name.charAt(0) }}
              </div>
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
              <div class="avatar-sm" :style="{ background: getAvatarGradient(currentFriend.friend_id) }">
                {{ currentFriend.name.charAt(0) }}
              </div>
              <div class="bubble assistant-bubble">
                <div class="bubble-text streaming-text">
                  <MarkdownRenderer :content="chatStore.streamingContent" /><span class="cursor" />
                </div>
              </div>
            </div>
          </div>

          <!-- Input Area -->
          <div class="input-area">
            <div class="input-wrapper">
              <textarea
                ref="inputRef"
                v-model="inputText"
                class="chat-input"
                :placeholder="`对${currentFriend.name}说...`"
                rows="1"
                :disabled="chatStore.streaming"
                @keydown="handleKeydown"
                @input="autoResize"
              />
              <div class="input-actions">
                <button
                  v-if="chatStore.streaming"
                  class="btn-stop"
                  @click="cancelStream"
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

    <!-- Create Friend Dialog -->
    <CreateFriendDialog
      :visible="showCreateDialog"
      @close="showCreateDialog = false"
      @created="onFriendCreated"
    />

    <!-- Material Dialog -->
    <MaterialDialog
      v-if="currentFriend"
      :visible="showMaterialDialog"
      :friend="currentFriend"
      @close="showMaterialDialog = false"
      @updated="onMaterialUpdated"
    />

    <!-- Settings Dialog -->
    <FriendSettingsDialog
      v-if="currentFriend"
      :visible="showSettingsDialog"
      :friend="currentFriend"
      @close="showSettingsDialog = false"
      @updated="onFriendUpdated"
    />

    <!-- Calibration Dialog -->
    <CalibrationDialog
      v-if="currentFriend"
      :visible="showCalibrationDialog"
      :friend="currentFriend"
      @close="showCalibrationDialog = false"
      @completed="onCalibrationCompleted"
    />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import CreateFriendDialog from '@/components/CreateFriendDialog.vue'
import MaterialDialog from '@/components/MaterialDialog.vue'
import FriendSettingsDialog from '@/components/FriendSettingsDialog.vue'
import CalibrationDialog from '@/components/CalibrationDialog.vue'
import * as friendApi from '@/api/friend'
import request from '@/utils/request'

const chatStore = useChatStore()

// State
const friends = ref([])
const currentFriend = ref(null)
const currentChatId = ref(null)
const messages = ref([])
const inputText = ref('')
const distillStatus = ref(null)
const pollingTimer = ref(null)
const panelOpen = ref(false)

// Dialog states
const showCreateDialog = ref(false)
const showMaterialDialog = ref(false)
const showSettingsDialog = ref(false)
const showCalibrationDialog = ref(false)

// Refs
const messagesRef = ref(null)
const inputRef = ref(null)

// Avatar gradient colors
const gradients = [
  'linear-gradient(135deg, #8b5cf6, #7c3aed)',
  'linear-gradient(135deg, #a855f7, #9333ea)',
  'linear-gradient(135deg, #c084fc, #a855f7)',
  'linear-gradient(135deg, #7c3aed, #6d28d9)',
  'linear-gradient(135deg, #6366f1, #4f46e5)',
  'linear-gradient(135deg, #818cf8, #6366f1)',
]

function getAvatarGradient(id) {
  return gradients[id % gradients.length]
}

// Lifecycle
onMounted(() => {
  fetchFriends()
})

onUnmounted(() => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
  }
})

// Fetch friends list
async function fetchFriends() {
  try {
    const res = await friendApi.listFriends({ page: 1, page_size: 100 })
    friends.value = res.data?.list || []
  } catch (error) {
    console.error('Failed to fetch friends:', error)
  }
}

// Select friend
async function selectFriend(friend) {
  currentFriend.value = friend
  distillStatus.value = null
  messages.value = []
  currentChatId.value = null
  panelOpen.value = false

  // Check distill status
  await checkDistillStatus()

  // Try to find or create a chat session for this friend
  await loadOrCreateSession(friend.friend_id)
}

// Load or create chat session for friend
async function loadOrCreateSession(friendId) {
  try {
    // Try to find existing session for this friend
    const res = await request({
      url: '/v1/chat/list',
      method: 'get',
      params: { page: 1, page_size: 100, app_type: 'digital_friend' }
    })
    const sessions = res.data?.list || []

    // Find session with this friend_id
    const existingSession = sessions.find(s => s.friend_id === friendId)

    if (existingSession) {
      currentChatId.value = existingSession.chat_id
      // Load messages
      await loadMessages(currentChatId.value)
    } else {
      // Create new session
      await createSession(friendId)
    }
  } catch (error) {
    console.error('Failed to load session:', error)
  }
}

// Create new chat session
async function createSession(friendId) {
  try {
    const res = await chatStore.createSession({
      app_type: 'digital_friend',
      friend_id: friendId,
      title: `与朋友的对话`
    })
    currentChatId.value = res.chat_id
    messages.value = []
  } catch (error) {
    const msg = error?.message || ''
    if (msg.includes('尚未完成人格蒸馏')) {
      ElMessage.warning('请先点击「生成人格」按钮完成训练')
    } else if (msg) {
      ElMessage.error(msg)
    }
  }
}

// Load messages
async function loadMessages(chat_id) {
  try {
    const res = await request({
      url: `/v1/chat/${chat_id}/messages`,
      method: 'get',
      params: { page: 1, page_size: 50 }
    })
    const list = res.data?.list || []
    messages.value = list.reverse()
  } catch (error) {
    console.error('Failed to load messages:', error)
  }
}

// Create friend
function onFriendCreated(friend) {
  friends.value.unshift(friend)
  selectFriend(friend)
  showCreateDialog.value = false
  ElMessage.success('朋友创建成功')
}

// Update friend
function onFriendUpdated(updatedFriend) {
  const index = friends.value.findIndex(f => f.friend_id === updatedFriend.friend_id)
  if (index !== -1) {
    friends.value[index] = { ...friends.value[index], ...updatedFriend }
  }
  if (currentFriend.value?.friend_id === updatedFriend.friend_id) {
    currentFriend.value = { ...currentFriend.value, ...updatedFriend }
  }
  showSettingsDialog.value = false
}

// Delete friend
async function handleDeleteFriend(friend) {
  try {
    await ElMessageBox.confirm(
      `确定要删除「${friend.name}」吗？此操作不可恢复。`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await friendApi.deleteFriend(friend.friend_id)
    friends.value = friends.value.filter(f => f.friend_id !== friend.friend_id)
    if (currentFriend.value?.friend_id === friend.friend_id) {
      currentFriend.value = null
      currentChatId.value = null
      messages.value = []
    }
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// Material updated
function onMaterialUpdated() {
  showMaterialDialog.value = false
  ElMessage.success('素材更新成功')
}

// Distill personality
async function handleDistill() {
  try {
    distillStatus.value = 'processing'
    await friendApi.distillFriend(currentFriend.value.friend_id)
    startPollingStatus()
  } catch (error) {
    distillStatus.value = null
    const msg = error?.message || ''
    if (msg.includes('请先上传素材') || msg.includes('素材')) {
      ElMessage.warning('请先添加素材，再生成人格')
    } else if (msg.includes('尚未完成人格蒸馏')) {
      ElMessage.warning('该朋友尚未完成人格训练')
    } else if (msg) {
      ElMessage.error(msg)
    }
  }
}

// Check distill status
async function checkDistillStatus() {
  if (!currentFriend.value) return
  try {
    const res = await friendApi.getFriendStatus(currentFriend.value.friend_id)
    console.log('Status API response:', res)
    const newStatus = res.data?.status
    console.log('New status:', newStatus, 'Current status:', distillStatus.value)
    distillStatus.value = newStatus
    // 蒸馏完成后进入校准阶段
    if (newStatus === 'calibrating') {
      showCalibrationDialog.value = true
    }
  } catch (error) {
    console.error('Failed to check status:', error)
  }
}

// Start polling status (第一阶段：等待进入校准)
function startPollingStatus() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
  }
  pollingTimer.value = setInterval(async () => {
    await checkDistillStatus()
    // 当进入校准阶段或失败时停止轮询
    if (distillStatus.value !== 'processing') {
      clearInterval(pollingTimer.value)
      pollingTimer.value = null
    }
  }, 2000)
}

// Start polling for final result (第二阶段：等待最终结果)
function startPollingFinalResult() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
  }
  pollingTimer.value = setInterval(async () => {
    await checkDistillStatus()
    // 当完成或失败时停止轮询
    if (distillStatus.value === 'ready' || distillStatus.value === 'failed' || !distillStatus.value) {
      clearInterval(pollingTimer.value)
      pollingTimer.value = null
      if (distillStatus.value === 'ready') {
        ElMessage.success('人格训练完成！现在可以开始聊天了')
      } else if (distillStatus.value === 'failed') {
        ElMessage.error('人格训练失败，请重试')
      }
    }
  }, 2000)
}

// Calibration completed - 关闭校准对话框，继续轮询最终结果
function onCalibrationCompleted() {
  showCalibrationDialog.value = false
  // 继续轮询，等待最终人格生成完成
  startPollingFinalResult()
}

// Send message using chat store
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || chatStore.streaming) return

  if (!currentChatId.value) {
    ElMessage.error('会话未初始化，请稍后重试')
    return
  }

  inputText.value = ''
  resetTextareaHeight()

  // Set current chat in store
  chatStore.currentChatId = currentChatId.value

  // Add user message to local list
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: text,
    createTime: new Date().toISOString()
  })

  nextTick(scrollToBottom)

  // Use chat store to send message
  await chatStore.sendMessage(text)

  // Update local messages from store
  messages.value = [...chatStore.messages]
  nextTick(scrollToBottom)
}

// Cancel stream
function cancelStream() {
  chatStore.cancelStream()
}

// Handle keydown
function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// Auto resize textarea
function autoResize() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

function resetTextareaHeight() {
  const el = inputRef.value
  if (el) el.style.height = 'auto'
}

// Scroll to bottom
function scrollToBottom() {
  const el = messagesRef.value
  if (el) el.scrollTop = el.scrollHeight
}

// Format time
function formatTime(time) {
  if (!time) return ''
  const d = new Date(time)
  if (isNaN(d.getTime())) return ''
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

// Watch for streaming changes to update messages
watch(
  () => [chatStore.messages.length, chatStore.streamingContent, chatStore.thinkingContent],
  () => {
    messages.value = [...chatStore.messages]
    nextTick(scrollToBottom)
  }
)
</script>

<style scoped>
.digital-friend {
  height: 100%;
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

/* ---- Main Container ---- */
.main-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* ---- Friends Panel ---- */
.friends-panel {
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
  background: #8b5cf6;
  color: white;
  border-radius: var(--border-radius);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  transition: all var(--duration-fast);
}

.btn-new:hover {
  background: #7c3aed;
  transform: translateY(-1px);
}

.btn-new svg {
  width: 14px;
  height: 14px;
}

.friends-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2);
}

.friend-item {
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

.friend-item:hover {
  background: var(--color-surface-hover);
}

.friend-item.active {
  background: rgba(139, 92, 246, 0.08);
}

.friend-avatar {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  border-radius: 50%;
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  flex-shrink: 0;
}

.friend-info {
  flex: 1;
  min-width: 0;
}

.friend-name {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.friend-desc {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-ink-faint);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.friend-delete {
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

.friend-item:hover .friend-delete {
  opacity: 1;
}

.friend-delete:hover {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.friend-delete svg {
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
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c4b5fd;
}

.empty-icon svg {
  width: 32px;
  height: 32px;
}

.panel-empty p {
  font-size: var(--text-sm);
}

.btn-create {
  padding: var(--space-2) var(--space-4);
  background: #8b5cf6;
  color: white;
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  transition: all var(--duration-fast);
}

.btn-create:hover {
  background: #7c3aed;
}

/* ---- Content Main ---- */
.content-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--color-bg);
}

/* ---- No Friend Selected ---- */
.no-friend {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
}

.no-friend-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 92, 246, 0.08);
  color: #8b5cf6;
  border-radius: 50%;
  opacity: 0.6;
}

.no-friend-icon svg {
  width: 28px;
  height: 28px;
}

.no-friend h3 {
  font-size: var(--text-lg);
  font-weight: var(--weight-medium);
  color: var(--color-ink);
}

.no-friend p {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
}

/* ---- Friend Header ---- */
.friend-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.header-avatar {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  border-radius: 50%;
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  flex-shrink: 0;
}

.header-details {
  flex: 1;
  min-width: 0;
}

.header-name {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
}

.header-desc {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.btn-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius);
  color: var(--color-ink-muted);
  transition: all var(--duration-fast);
}

.btn-icon:hover {
  background: var(--color-surface-hover);
  color: var(--color-ink);
}

.btn-icon svg {
  width: 18px;
  height: 18px;
}

.btn-distill {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: #8b5cf6;
  color: white;
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  transition: all var(--duration-fast);
}

.btn-distill:hover:not(:disabled) {
  background: #7c3aed;
}

.btn-distill:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-distill svg {
  width: 16px;
  height: 16px;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ---- Welcome ---- */
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
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 32px;
  font-weight: var(--weight-semibold);
  border-radius: 50%;
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.3);
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

.welcome-hint {
  margin-top: var(--space-4);
  padding: var(--space-4);
  background: rgba(139, 92, 246, 0.06);
  border-radius: var(--border-radius-lg);
  max-width: 400px;
}

.welcome-hint p {
  font-size: var(--text-sm);
  color: #7c3aed;
  line-height: var(--leading-relaxed);
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

.user-row {
  justify-content: flex-end;
}

.assistant-row {
  justify-content: flex-start;
}

/* ---- Avatar ---- */
.avatar-sm {
  width: 32px;
  height: 32px;
  border-radius: 50%;
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
  background: #8b5cf6;
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

/* ---- Thinking ---- */
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
  background: #8b5cf6;
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

/* ---- Streaming ---- */
.streaming-text {
  position: relative;
}

.cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: #8b5cf6;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
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
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.08);
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
  background: #8b5cf6;
  color: white;
  transition: all var(--duration-fast);
}

.btn-send:hover:not(:disabled) {
  background: #7c3aed;
  transform: scale(1.05);
  box-shadow: 0 0 16px rgba(139, 92, 246, 0.4);
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
  color: #8b5cf6;
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

  .friends-panel {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: 280px;
    z-index: var(--z-sticky);
    transform: translateX(-100%);
    transition: transform var(--duration-slow) var(--ease-out);
  }

  .friends-panel.open {
    transform: translateX(0);
  }

  .panel-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: calc(var(--z-sticky) - 1);
  }

  .main-container {
    position: relative;
    height: calc(100vh - var(--header-height));
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

  .welcome {
    padding: var(--space-6) var(--space-4);
  }

  .friend-header {
    padding: var(--space-3) var(--space-4);
    flex-wrap: wrap;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
    margin-top: var(--space-2);
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
