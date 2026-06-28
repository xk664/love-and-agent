<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="dialog-overlay" @click.self="close">
        <Transition name="scale">
          <div v-if="visible" class="dialog-card">
            <!-- Header -->
            <div class="dialog-header">
              <h3>新建对话</h3>
              <button class="dialog-close" @click="close">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Body -->
            <div class="dialog-body">
              <!-- App Type -->
              <div class="form-section">
                <label class="form-label">选择类型</label>
                <div class="type-options">
                  <button
                    class="type-btn"
                    :class="{ active: form.app_type === 'love_app' }"
                    @click="form.app_type = 'love_app'"
                  >
                    <div class="type-icon love">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                      </svg>
                    </div>
                    <span class="type-name">恋爱大师</span>
                    <span class="type-desc">情感陪伴与恋爱指导</span>
                  </button>
                  <button
                    class="type-btn"
                    :class="{ active: form.app_type === 'manus' }"
                    @click="form.app_type = 'manus'"
                  >
                    <div class="type-icon agent">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                      </svg>
                    </div>
                    <span class="type-name">超级智能体</span>
                    <span class="type-desc">自主规划，完成复杂任务</span>
                  </button>
                </div>
              </div>

              <!-- Emotion Status (Love Master only) -->
              <Transition name="slide">
                <div v-if="form.app_type === 'love_app'" class="form-section">
                  <label class="form-label">你的情感状态</label>
                  <p class="form-hint">选定后不可更改，帮助大师更好地理解你</p>
                  <div class="emotion-options">
                    <button
                      v-for="opt in emotionOptions"
                      :key="opt.value"
                      class="emotion-btn"
                      :class="{ active: form.emotion_status === opt.value }"
                      @click="form.emotion_status = opt.value"
                    >
                      <span class="emotion-icon">{{ opt.icon }}</span>
                      <span class="emotion-label">{{ opt.label }}</span>
                      <span class="emotion-desc">{{ opt.desc }}</span>
                    </button>
                  </div>
                  <p v-if="showError && !form.emotion_status" class="field-hint">
                    请选择情感状态，以便更好地为你提供建议
                  </p>
                </div>
              </Transition>
            </div>

            <!-- Footer -->
            <div class="dialog-footer">
              <button class="btn-cancel" @click="close">取消</button>
              <button
                class="btn-confirm"
                :disabled="!canSubmit || submitting"
                @click="handleCreate"
              >
                {{ submitting ? '创建中...' : '创建' }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useChatStore } from '@/stores/chat'

const props = defineProps({
  visible: { type: Boolean, default: false },
  defaultType: { type: String, default: 'love_app' }
})

const emit = defineEmits(['close', 'created'])

const chatStore = useChatStore()
const submitting = ref(false)
const showError = ref(false)

const form = reactive({
  app_type: props.defaultType,
  emotion_status: ''
})

const emotionOptions = [
  { value: 'single', label: '单身', icon: '☆', desc: '享受自由，寻找方向' },
  { value: 'relationship', label: '恋爱中', icon: '♡', desc: '甜蜜时光，用心经营' },
  { value: 'married', label: '已婚', icon: '♥', desc: '携手同行，细水长流' }
]

const canSubmit = computed(() => {
  if (!form.app_type) return false
  if (form.app_type === 'love_app' && !form.emotion_status) return false
  return true
})

// Reset form when dialog opens
watch(() => props.visible, (val) => {
  if (val) {
    form.app_type = props.defaultType
    form.emotion_status = ''
    showError.value = false
    submitting.value = false
  }
})

function close() {
  emit('close')
}

async function handleCreate() {
  if (!canSubmit.value) {
    showError.value = true
    return
  }

  submitting.value = true
  try {
    const data = {
      app_type: form.app_type
    }
    if (form.app_type === 'love_app') {
      data.emotion_status = form.emotion_status
    }
    const session = await chatStore.createSession(data)
    emit('created', session)
    close()
  } catch {
    // error handled by request interceptor
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-6);
}

.dialog-card {
  width: 100%;
  max-width: 440px;
  background: var(--color-surface);
  border-radius: var(--border-radius-xl);
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border-light);
}

.dialog-header h3 {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
}

.dialog-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius);
  color: var(--color-ink-muted);
  transition: all var(--duration-fast);
}

.dialog-close:hover {
  background: var(--color-surface-hover);
  color: var(--color-ink);
}

.dialog-close svg {
  width: 16px;
  height: 16px;
}

.dialog-body {
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

/* ---- Form ---- */
.form-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.form-label {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-ink);
}

/* ---- Type Options ---- */
.type-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}

.type-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-5) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-lg);
  transition: all var(--duration-fast);
  background: var(--color-surface);
}

.type-btn:hover {
  border-color: var(--color-border-hover);
  background: var(--color-surface-hover);
}

.type-btn.active {
  border-color: var(--color-accent);
  background: var(--color-accent-bg);
}

.type-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius);
}

.type-icon svg {
  width: 20px;
  height: 20px;
}

.type-icon.love {
  background: linear-gradient(135deg, #fdf2f8, #fce7f3);
  color: #ec4899;
}

.type-icon.agent {
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  color: #3b82f6;
}

.type-btn.active .type-icon.love {
  background: linear-gradient(135deg, #fce7f3, #fbcfe8);
}

.type-btn.active .type-icon.agent {
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
}

.type-name {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
}

.type-desc {
  font-size: 11px;
  color: var(--color-ink-muted);
  text-align: center;
  line-height: var(--leading-tight);
}

/* ---- Emotion Options ---- */
.form-hint {
  font-size: var(--text-xs);
  color: var(--color-ink-muted);
  margin-top: calc(-1 * var(--space-1));
}

.emotion-options {
  display: flex;
  gap: var(--space-3);
}

.emotion-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-2);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-lg);
  transition: all var(--duration-normal) var(--ease-out);
  background: var(--color-surface);
}

.emotion-btn:hover {
  border-color: var(--color-border-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.emotion-btn.active {
  border-color: var(--color-accent);
  background: var(--color-accent-bg);
  transform: translateY(-2px);
}

.emotion-icon {
  font-size: 24px;
  color: var(--color-ink-faint);
  transition: all var(--duration-normal);
}

.emotion-btn.active .emotion-icon {
  color: var(--color-accent);
  transform: scale(1.15);
}

.emotion-label {
  font-size: var(--text-sm);
  color: var(--color-ink);
  font-weight: var(--weight-semibold);
}

.emotion-desc {
  font-size: 11px;
  color: var(--color-ink-muted);
  text-align: center;
  line-height: var(--leading-tight);
  transition: color var(--duration-fast);
}

.emotion-btn.active .emotion-desc {
  color: var(--color-accent-dark);
}

.field-hint {
  font-size: var(--text-xs);
  color: var(--color-accent-dark);
}

/* ---- Footer ---- */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--color-border-light);
}

.btn-cancel {
  padding: var(--space-2) var(--space-5);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  transition: all var(--duration-fast);
}

.btn-cancel:hover {
  background: var(--color-surface-hover);
  color: var(--color-ink);
}

.btn-confirm {
  padding: var(--space-2) var(--space-6);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  background: var(--color-primary);
  color: white;
  transition: all var(--duration-fast);
}

.btn-confirm:hover:not(:disabled) {
  background: var(--color-primary-light);
  transform: translateY(-1px);
}

.btn-confirm:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ---- Transitions ---- */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--duration-normal) var(--ease-out);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.scale-enter-active,
.scale-leave-active {
  transition: all var(--duration-slow) var(--ease-spring);
}

.scale-enter-from,
.scale-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(8px);
}

.slide-enter-active,
.slide-leave-active {
  transition: all var(--duration-normal) var(--ease-out);
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  padding-top: 0;
}

.slide-enter-to,
.slide-leave-from {
  max-height: 200px;
}
</style>
