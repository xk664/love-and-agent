<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="dialog-overlay" @click.self="$emit('close')">
        <div class="dialog">
          <div class="dialog-header">
            <h3 class="dialog-title">朋友设置</h3>
            <button class="btn-close" @click="$emit('close')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="dialog-body">
            <div class="form-group">
              <label class="form-label">朋友昵称</label>
              <input
                v-model="form.name"
                class="form-input"
                placeholder="朋友昵称"
                maxlength="64"
              />
            </div>

            <div class="form-group">
              <label class="form-label">一句话描述</label>
              <textarea
                v-model="form.description"
                class="form-textarea"
                placeholder="用一句话描述这个朋友"
                maxlength="500"
                rows="2"
              />
            </div>

            <div class="form-group">
              <label class="form-label">人格状态</label>
              <div class="status-display">
                <span class="status-badge" :class="friend.status || 'draft'">
                  {{ getStatusLabel(friend.status) }}
                </span>
                <span class="status-hint">{{ getStatusHint(friend.status) }}</span>
              </div>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="btn-cancel" @click="$emit('close')">取消</button>
            <button
              class="btn-save"
              :disabled="!hasChanges || saving"
              @click="handleSave"
            >
              <span v-if="saving" class="spinner" />
              <span>{{ saving ? '保存中...' : '保存' }}</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as friendApi from '@/api/friend'

const props = defineProps({
  visible: Boolean,
  friend: Object
})

const emit = defineEmits(['close', 'updated'])

const saving = ref(false)
const form = reactive({
  name: '',
  description: ''
})

const hasChanges = computed(() => {
  return form.name !== (props.friend?.name || '') ||
         form.description !== (props.friend?.description || '')
})

watch(() => props.visible, (val) => {
  if (val && props.friend) {
    form.name = props.friend.name || ''
    form.description = props.friend.description || ''
  }
})

function getStatusLabel(status) {
  const labels = {
    draft: '草稿',
    pending: '待训练',
    processing: '训练中',
    ready: '就绪',
    failed: '失败'
  }
  return labels[status] || '未知'
}

function getStatusHint(status) {
  const hints = {
    draft: '添加素材后点击「生成人格」开始训练',
    pending: '正在等待训练...',
    processing: 'AI正在分析素材并生成人格...',
    ready: '人格已生成，可以开始聊天了',
    failed: '训练失败，请重新尝试'
  }
  return hints[status] || ''
}

async function handleSave() {
  if (!hasChanges.value) return

  saving.value = true
  try {
    const data = {}
    if (form.name !== props.friend.name) {
      data.name = form.name.trim()
    }
    if (form.description !== (props.friend.description || '')) {
      data.description = form.description.trim() || null
    }

    await friendApi.updateFriend(props.friend.friend_id, data)
    emit('updated', { ...props.friend, ...data })
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}
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
  width: 420px;
  max-width: calc(100vw - 32px);
  background: var(--color-surface);
  border-radius: var(--border-radius-xl);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-border-light);
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
  padding: var(--space-6);
}

.form-group {
  margin-bottom: var(--space-5);
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-ink);
  margin-bottom: var(--space-2);
}

.form-input,
.form-textarea {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: var(--text-base);
  color: var(--color-ink);
  transition: border-color var(--duration-fast), box-shadow var(--duration-fast);
}

.form-input:focus,
.form-textarea:focus {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.08);
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: var(--color-ink-faint);
}

.form-textarea {
  resize: none;
  min-height: 60px;
}

.status-display {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.status-badge {
  display: inline-flex;
  align-self: flex-start;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--border-radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
}

.status-badge.draft {
  background: var(--color-bg);
  color: var(--color-ink-muted);
}

.status-badge.pending {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.status-badge.processing {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.status-badge.ready {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.status-badge.failed {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.status-hint {
  font-size: var(--text-xs);
  color: var(--color-ink-faint);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  background: var(--color-bg);
  border-top: 1px solid var(--color-border-light);
}

.btn-cancel {
  padding: var(--space-2) var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-ink-muted);
  transition: all var(--duration-fast);
}

.btn-cancel:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-border-hover);
  color: var(--color-ink);
}

.btn-save {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-5);
  background: #8b5cf6;
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: white;
  transition: all var(--duration-fast);
}

.btn-save:hover:not(:disabled) {
  background: #7c3aed;
}

.btn-save:disabled {
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
