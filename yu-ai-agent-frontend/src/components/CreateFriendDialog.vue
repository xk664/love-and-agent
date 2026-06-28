<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="dialog-overlay" @click.self="$emit('close')">
        <div class="dialog">
          <div class="dialog-header">
            <h3 class="dialog-title">创建数字朋友</h3>
            <button class="btn-close" @click="$emit('close')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="dialog-body">
            <div class="form-group">
              <label class="form-label">朋友昵称 <span class="required">*</span></label>
              <input
                v-model="form.name"
                class="form-input"
                placeholder="给他/她起个名字"
                maxlength="64"
              />
              <span class="form-hint">1-64个字符</span>
            </div>

            <div class="form-group">
              <label class="form-label">一句话描述</label>
              <textarea
                v-model="form.description"
                class="form-textarea"
                placeholder="用一句话描述这个朋友（可选）"
                maxlength="500"
                rows="2"
              />
              <span class="form-hint">最多500个字符</span>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="btn-cancel" @click="$emit('close')">取消</button>
            <button
              class="btn-confirm"
              :disabled="!form.name.trim() || loading"
              @click="handleCreate"
            >
              <span v-if="loading" class="spinner" />
              <span>{{ loading ? '创建中...' : '创建' }}</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import * as friendApi from '@/api/friend'

const props = defineProps({
  visible: Boolean
})

const emit = defineEmits(['close', 'created'])

const loading = ref(false)
const form = reactive({
  name: '',
  description: ''
})

async function handleCreate() {
  if (!form.name.trim()) return

  loading.value = true
  try {
    const res = await friendApi.createFriend({
      name: form.name.trim(),
      description: form.description.trim() || null
    })
    emit('created', res.data)
    resetForm()
  } catch (error) {
    ElMessage.error('创建失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.name = ''
  form.description = ''
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

.required {
  color: var(--color-danger);
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

.form-hint {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-ink-faint);
  margin-top: var(--space-1);
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

.btn-confirm {
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

.btn-confirm:hover:not(:disabled) {
  background: #7c3aed;
}

.btn-confirm:disabled {
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
