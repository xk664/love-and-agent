<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="dialog-overlay" @click.self="$emit('close')">
        <div class="dialog dialog-large">
          <div class="dialog-header">
            <h3 class="dialog-title">管理素材 - {{ friend.name }}</h3>
            <button class="btn-close" @click="$emit('close')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="dialog-body">
            <!-- Material Type Tabs -->
            <div class="type-tabs">
              <button
                v-for="type in materialTypes"
                :key="type.value"
                class="type-tab"
                :class="{ active: activeTab === type.value }"
                @click="activeTab = type.value"
              >
                <span class="tab-icon" v-html="type.icon" />
                <span class="tab-label">{{ type.label }}</span>
              </button>
            </div>

            <!-- Add Material Form -->
            <div class="add-section">
              <!-- 聊天记录专用：指定自己是谁 -->
              <div v-if="activeTab === 'chat_log'" class="self-name-row">
                <label class="form-label">聊天记录中哪个是你？</label>
                <input
                  v-model="selfName"
                  class="self-name-input"
                  placeholder="例如：小明、我、A"
                  maxlength="20"
                />
                <span class="form-hint">填写聊天中代表你的名字或昵称，用于区分双方身份</span>
              </div>
              <div class="input-row">
                <textarea
                  v-model="newContent"
                  class="material-input"
                  :placeholder="getPlaceholder(activeTab)"
                  rows="3"
                />
              </div>
              <div class="action-row">
                <label class="upload-btn">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  <span>上传文件</span>
                  <input
                    type="file"
                    accept=".txt,.csv,.md"
                    class="file-input"
                    @change="handleFileUpload"
                  />
                </label>
                <button
                  class="add-btn"
                  :disabled="!newContent.trim() || adding"
                  @click="handleAddText"
                >
                  <span v-if="adding" class="spinner" />
                  <span>{{ adding ? '添加中...' : '添加文本' }}</span>
                </button>
              </div>
            </div>

            <!-- Materials List -->
            <div class="materials-section">
              <div class="section-header">
                <span class="section-title">已添加的素材</span>
                <span class="section-count">{{ filteredMaterials.length }} 条</span>
              </div>

              <div class="materials-list" v-if="filteredMaterials.length > 0">
                <div
                  v-for="(material, index) in filteredMaterials"
                  :key="index"
                  class="material-item"
                >
                  <div class="material-content">
                    <span class="material-type-badge">{{ getTypeLabel(material.type) }}</span>
                    <span v-if="material.self_name" class="material-self-name">我: {{ material.self_name }}</span>
                    <p class="material-text">{{ truncateText(material.content, 150) }}</p>
                    <span v-if="material.title" class="material-title">{{ material.title }}</span>
                  </div>
                  <button
                    class="material-delete"
                    @click="handleDeleteMaterial(index)"
                    title="删除"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                    </svg>
                  </button>
                </div>
              </div>

              <div class="materials-empty" v-else>
                <p>还没有添加{{ getTypeLabel(activeTab) }}素材</p>
                <p class="empty-hint">添加素材可以帮助AI更好地了解这个朋友</p>
              </div>
            </div>
          </div>

          <div class="dialog-footer">
            <div class="footer-info">
              <span class="info-tip">💡 素材越丰富，生成的人格越准确</span>
            </div>
            <button class="btn-done" @click="$emit('close')">完成</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as friendApi from '@/api/friend'

const props = defineProps({
  visible: Boolean,
  friend: Object
})

const emit = defineEmits(['close', 'updated'])

const activeTab = ref('chat_log')
const newContent = ref('')
const selfName = ref('')
const adding = ref(false)
const materials = ref([])

const materialTypes = [
  { value: 'chat_log', label: '聊天记录', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>' },
  { value: 'moments', label: '朋友圈', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>' },
  { value: 'hobby', label: '兴趣爱好', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>' },
  { value: 'habit', label: '生活习惯', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>' },
  { value: 'description', label: '人物描述', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' },
]

const filteredMaterials = computed(() => {
  return materials.value.filter(m => m.type === activeTab.value)
})

function getPlaceholder(type) {
  const placeholders = {
    chat_log: '粘贴聊天记录，每条一行...',
    moments: '粘贴朋友圈内容...',
    hobby: '描述兴趣爱好，如：喜欢打篮球、看电影...',
    habit: '描述生活习惯，如：每天早起跑步...',
    description: '描述人物特征，如：性格开朗、爱笑...'
  }
  return placeholders[type] || '输入内容...'
}

function getTypeLabel(type) {
  const found = materialTypes.find(t => t.value === type)
  return found ? found.label : type
}

function truncateText(text, max) {
  if (!text) return ''
  return text.length > max ? text.slice(0, max) + '...' : text
}

async function handleAddText() {
  if (!newContent.value.trim()) return

  adding.value = true
  try {
    const material = { type: activeTab.value, content: newContent.value.trim() }
    // 聊天记录类型添加 self_name 字段
    if (activeTab.value === 'chat_log' && selfName.value.trim()) {
      material.self_name = selfName.value.trim()
    }
    await friendApi.addSource(props.friend.friend_id, [material])
    materials.value.push(material)
    newContent.value = ''
    ElMessage.success('素材添加成功')
  } catch (error) {
    ElMessage.error('添加失败，请稍后重试')
  } finally {
    adding.value = false
  }
}

async function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  const allowedExts = ['.txt', '.csv', '.md']
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
  if (!allowedExts.includes(ext)) {
    ElMessage.error('仅支持 .txt, .csv, .md 格式')
    return
  }

  try {
    await friendApi.uploadSourceFile(props.friend.friend_id, file, {
      source_type: activeTab.value
    })
    const content = await file.text()
    materials.value.push({
      type: activeTab.value,
      content: content,
      title: file.name
    })
    ElMessage.success('文件上传成功')
  } catch (error) {
    ElMessage.error('上传失败，请稍后重试')
  }

  event.target.value = ''
}

function handleDeleteMaterial(index) {
  const actualIndex = materials.value.findIndex(
    (m, i) => m.type === activeTab.value && getFilteredIndex(i) === index
  )
  if (actualIndex !== -1) {
    materials.value.splice(actualIndex, 1)
  }
}

function getFilteredIndex(realIndex) {
  let count = 0
  for (let i = 0; i < realIndex; i++) {
    if (materials.value[i].type === activeTab.value) {
      count++
    }
  }
  return count
}

onMounted(async () => {
  if (props.friend?.friend_id) {
    try {
      const res = await friendApi.getFriend(props.friend.friend_id)
      materials.value = res.data?.materials || []
    } catch (error) {
      console.error('Failed to load materials:', error)
    }
  }
})
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  backdrop-filter: blur(4px);
}

.dialog {
  width: 480px;
  max-width: calc(100vw - 32px);
  background: var(--color-surface);
  border-radius: var(--border-radius-xl);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 80vh;
}

.dialog-large {
  width: 560px;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-border-light);
  flex-shrink: 0;
}

.dialog-title {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
}

.btn-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius);
  color: var(--color-ink-muted);
  transition: all var(--duration-fast);
}

.btn-close:hover {
  background: var(--color-surface-hover);
  color: var(--color-ink);
}

.btn-close svg {
  width: 18px;
  height: 18px;
}

.dialog-body {
  padding: var(--space-5) var(--space-6);
  overflow-y: auto;
  flex: 1;
}

/* Type Tabs */
.type-tabs {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-5);
  flex-wrap: wrap;
}

.type-tab {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  transition: all var(--duration-fast);
}

.type-tab:hover {
  border-color: #c4b5fd;
  color: #7c3aed;
}

.type-tab.active {
  background: rgba(139, 92, 246, 0.08);
  border-color: #8b5cf6;
  color: #7c3aed;
}

.tab-icon {
  width: 16px;
  height: 16px;
  display: flex;
}

.tab-icon :deep(svg) {
  width: 100%;
  height: 100%;
}

/* Add Section */
.add-section {
  margin-bottom: var(--space-5);
}

.input-row {
  margin-bottom: var(--space-3);
}

/* Self Name Input */
.self-name-row {
  margin-bottom: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: rgba(139, 92, 246, 0.06);
  border-radius: var(--border-radius);
}

.self-name-row .form-label {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-ink);
  margin-bottom: var(--space-2);
}

.self-name-input {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  color: var(--color-ink);
  transition: border-color var(--duration-fast), box-shadow var(--duration-fast);
}

.self-name-input:focus {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.08);
}

.self-name-input::placeholder {
  color: var(--color-ink-faint);
}

.self-name-row .form-hint {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-ink-faint);
  margin-top: var(--space-1);
}

.material-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: var(--text-base);
  color: var(--color-ink);
  resize: none;
  transition: border-color var(--duration-fast), box-shadow var(--duration-fast);
}

.material-input:focus {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.08);
}

.material-input::placeholder {
  color: var(--color-ink-faint);
}

.action-row {
  display: flex;
  gap: var(--space-3);
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  cursor: pointer;
  transition: all var(--duration-fast);
}

.upload-btn:hover {
  border-color: #c4b5fd;
  color: #7c3aed;
}

.upload-btn svg {
  width: 16px;
  height: 16px;
}

.file-input {
  display: none;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: #8b5cf6;
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: white;
  transition: all var(--duration-fast);
}

.add-btn:hover:not(:disabled) {
  background: #7c3aed;
}

.add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

/* Materials Section */
.materials-section {
  border-top: 1px solid var(--color-border-light);
  padding-top: var(--space-5);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.section-title {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
}

.section-count {
  font-size: var(--text-xs);
  color: var(--color-ink-faint);
}

.materials-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.material-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg);
  border-radius: var(--border-radius);
}

.material-content {
  flex: 1;
  min-width: 0;
}

.material-type-badge {
  display: inline-block;
  padding: 2px var(--space-2);
  background: rgba(139, 92, 246, 0.1);
  color: #7c3aed;
  font-size: var(--text-xs);
  border-radius: var(--border-radius);
  margin-bottom: var(--space-2);
}

.material-self-name {
  display: inline-block;
  padding: 2px var(--space-2);
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  font-size: var(--text-xs);
  border-radius: var(--border-radius);
  margin-left: var(--space-2);
  margin-bottom: var(--space-2);
}

.material-text {
  font-size: var(--text-sm);
  color: var(--color-ink);
  line-height: var(--leading-relaxed);
  word-break: break-word;
}

.material-title {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-ink-faint);
  margin-top: var(--space-1);
}

.material-delete {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius);
  color: var(--color-ink-faint);
  flex-shrink: 0;
  transition: all var(--duration-fast);
}

.material-delete:hover {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.material-delete svg {
  width: 14px;
  height: 14px;
}

.materials-empty {
  text-align: center;
  padding: var(--space-8) var(--space-4);
  color: var(--color-ink-muted);
}

.materials-empty p {
  font-size: var(--text-sm);
}

.empty-hint {
  font-size: var(--text-xs) !important;
  color: var(--color-ink-faint) !important;
  margin-top: var(--space-2);
}

/* Footer */
.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  background: var(--color-bg);
  border-top: 1px solid var(--color-border-light);
  flex-shrink: 0;
}

.footer-info {
  flex: 1;
}

.info-tip {
  font-size: var(--text-xs);
  color: var(--color-ink-faint);
}

.btn-done {
  padding: var(--space-2) var(--space-6);
  background: #8b5cf6;
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: white;
  transition: all var(--duration-fast);
}

.btn-done:hover {
  background: #7c3aed;
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--duration-normal) var(--ease-out);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .dialog,
.modal-leave-active .dialog {
  transition: transform var(--duration-normal) var(--ease-out),
              opacity var(--duration-normal) var(--ease-out);
}

.modal-enter-from .dialog {
  transform: scale(0.95);
  opacity: 0;
}

.modal-leave-to .dialog {
  transform: scale(0.95);
  opacity: 0;
}
</style>
