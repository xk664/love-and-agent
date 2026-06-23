<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="dialog-overlay" @click.self="close">
        <Transition name="scale">
          <div v-if="visible" class="dialog-card">
            <div class="dialog-header">
              <h3>新建对话</h3>
              <button class="dialog-close" @click="close">✕</button>
            </div>

            <div class="dialog-body">
              <!-- App Type -->
              <div class="form-section">
                <label class="form-label">选择类型</label>
                <div class="type-options">
                  <button
                    class="type-btn"
                    :class="{ active: form.appType === 'love_app', coral: form.appType === 'love_app' }"
                    @click="form.appType = 'love_app'"
                  >
                    <span class="type-icon">♡</span>
                    <span class="type-name">恋爱大师</span>
                    <span class="type-desc">情感陪伴与恋爱指导</span>
                  </button>
                  <button
                    class="type-btn"
                    :class="{ active: form.appType === 'manus', indigo: form.appType === 'manus' }"
                    @click="form.appType = 'manus'"
                  >
                    <span class="type-icon">◈</span>
                    <span class="type-name">超级智能体</span>
                    <span class="type-desc">自主规划，完成复杂任务</span>
                  </button>
                </div>
              </div>

              <!-- Emotion Status (Love Master only) -->
              <Transition name="slide">
                <div v-if="form.appType === 'love_app'" class="form-section">
                  <label class="form-label">你的情感状态</label>
                  <p class="form-hint">选定后不可更改，帮助大师更好地理解你</p>
                  <div class="emotion-options">
                    <button
                      v-for="opt in emotionOptions"
                      :key="opt.value"
                      class="emotion-btn"
                      :class="{ active: form.emotionStatus === opt.value }"
                      @click="form.emotionStatus = opt.value"
                    >
                      <span class="emotion-icon">{{ opt.icon }}</span>
                      <span class="emotion-label">{{ opt.label }}</span>
                      <span class="emotion-desc">{{ opt.desc }}</span>
                    </button>
                  </div>
                  <p v-if="showError && !form.emotionStatus" class="field-hint">
                    请选择情感状态，以便更好地为你提供建议
                  </p>
                </div>
              </Transition>
            </div>

            <div class="dialog-footer">
              <button class="btn-cancel" @click="close">取消</button>
              <button
                class="btn-confirm"
                :class="{ coral: form.appType === 'love_app', indigo: form.appType === 'manus' }"
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
import { ref, reactive, computed } from 'vue'
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
  appType: props.defaultType,
  emotionStatus: ''
})

const emotionOptions = [
  { value: 'single', label: '单身', icon: '☆', desc: '享受自由，寻找方向' },
  { value: 'relationship', label: '恋爱中', icon: '♡', desc: '甜蜜时光，用心经营' },
  { value: 'married', label: '已婚', icon: '♥', desc: '携手同行，细水长流' }
]

const canSubmit = computed(() => {
  if (!form.appType) return false
  if (form.appType === 'love_app' && !form.emotionStatus) return false
  return true
})

// Reset form when dialog opens
import { watch } from 'vue'
watch(() => props.visible, (val) => {
  if (val) {
    form.appType = props.defaultType
    form.emotionStatus = ''
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
      appType: form.appType
    }
    if (form.appType === 'love_app') {
      data.emotionStatus = form.emotionStatus
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
  background: var(--color-cloud);
  border-radius: var(--border-radius-xl);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-stone-bg);
}

.dialog-header h3 {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
}

.dialog-close {
  color: var(--color-stone);
  font-size: var(--text-lg);
  padding: var(--space-1);
  border-radius: var(--border-radius);
  transition: color var(--duration-fast);
}

.dialog-close:hover {
  color: var(--color-ink);
}

.dialog-body {
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
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
  border: 2px solid var(--color-stone-light);
  border-radius: var(--border-radius-lg);
  transition: all var(--duration-fast);
  background: var(--color-cloud);
}

.type-btn:hover {
  border-color: var(--color-stone);
}

.type-btn.active.coral {
  border-color: var(--color-coral);
  background: var(--color-coral-bg);
}

.type-btn.active.indigo {
  border-color: var(--color-indigo);
  background: var(--color-indigo-bg);
}

.type-icon {
  font-size: 24px;
}

.type-btn.active.coral .type-icon { color: var(--color-coral); }
.type-btn.active.indigo .type-icon { color: var(--color-indigo); }

.type-name {
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
}

.type-desc {
  font-size: var(--text-xs);
  color: var(--color-stone);
  text-align: center;
  line-height: var(--leading-tight);
}

/* ---- Emotion Options ---- */
.form-hint {
  font-size: var(--text-xs);
  color: var(--color-stone);
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
  padding: var(--space-5) var(--space-2);
  border: 2px solid var(--color-stone-light);
  border-radius: var(--border-radius-lg);
  transition: all var(--duration-normal) var(--ease-out);
  background: var(--color-cloud);
}

.emotion-btn:hover {
  border-color: var(--color-coral-light);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.emotion-btn.active {
  border-color: var(--color-coral);
  background: linear-gradient(135deg, rgba(232, 108, 138, 0.06), rgba(232, 108, 138, 0.12));
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow-coral);
}

.emotion-icon {
  font-size: 24px;
  color: var(--color-stone);
  transition: all var(--duration-normal);
}

.emotion-btn.active .emotion-icon {
  color: var(--color-coral);
  transform: scale(1.15);
}

.emotion-label {
  font-size: var(--text-sm);
  color: var(--color-ink);
  font-weight: var(--weight-semibold);
}

.emotion-desc {
  font-size: 11px;
  color: var(--color-stone);
  text-align: center;
  line-height: var(--leading-tight);
  transition: color var(--duration-fast);
}

.emotion-btn.active .emotion-desc {
  color: var(--color-coral);
}

.field-hint {
  font-size: var(--text-xs);
  color: var(--color-coral);
}

/* ---- Footer ---- */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--color-stone-bg);
}

.btn-cancel {
  padding: var(--space-2) var(--space-5);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  color: var(--color-stone);
  transition: color var(--duration-fast);
}

.btn-cancel:hover {
  color: var(--color-ink);
}

.btn-confirm {
  padding: var(--space-2) var(--space-6);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: white;
  transition: all var(--duration-fast);
}

.btn-confirm.coral { background: var(--color-coral); }
.btn-confirm.coral:hover:not(:disabled) { background: #d45a78; }
.btn-confirm.indigo { background: var(--color-indigo); }
.btn-confirm.indigo:hover:not(:disabled) { background: #4f46e5; }

.btn-confirm:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ---- Transitions ---- */
.scale-enter-active,
.scale-leave-active {
  transition: all var(--duration-normal) var(--ease-out);
}

.scale-enter-from,
.scale-leave-to {
  opacity: 0;
  transform: scale(0.95);
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
