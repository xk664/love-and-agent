<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="dialog-overlay" @click.self="handleClose">
        <div class="dialog dialog-large">
          <div class="dialog-header">
            <h3 class="dialog-title">人格校准 - {{ friend.name }}</h3>
            <button class="btn-close" @click="handleClose">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="dialog-body">
            <!-- Loading State -->
            <div v-if="loading" class="loading-state">
              <div class="loading-spinner" />
              <p>正在加载校准问题...</p>
            </div>

            <!-- Questions -->
            <template v-else>
              <div class="intro-section">
                <div class="intro-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                </div>
                <div class="intro-text">
                  <h4>完善人格特征</h4>
                  <p>回答以下问题可以帮助AI更准确地模拟{{ friend.name }}的性格和说话方式</p>
                </div>
              </div>

              <div class="questions-list">
                <div
                  v-for="(question, index) in questions"
                  :key="question.id || index"
                  class="question-item"
                >
                  <div class="question-number">{{ index + 1 }}</div>
                  <div class="question-content">
                    <p class="question-text">{{ question.question }}</p>
                    <p v-if="question.context" class="question-context">{{ question.context }}</p>
                    <textarea
                      v-model="answers[index]"
                      class="answer-input"
                      placeholder="写下你的回答..."
                      rows="2"
                    />
                  </div>
                </div>
              </div>
            </template>
          </div>

          <div class="dialog-footer">
            <div class="footer-left">
              <span class="progress-text">
                {{ answeredCount }}/{{ questions.length }} 已回答
              </span>
            </div>
            <div class="footer-right">
              <button class="btn-skip" @click="handleClose">稍后再说</button>
              <button
                class="btn-finalize"
                :disabled="answeredCount === 0 || finalizing"
                @click="handleFinalize"
              >
                <span v-if="finalizing" class="spinner" />
                <span>{{ finalizing ? '完成中...' : '完成校准' }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as friendApi from '@/api/friend'

const props = defineProps({
  visible: Boolean,
  friend: Object
})

const emit = defineEmits(['close', 'completed'])

const loading = ref(false)
const finalizing = ref(false)
const questions = ref([])
const answers = ref([])

const answeredCount = computed(() => {
  return answers.value.filter(a => a && a.trim()).length
})

// 监听 visible 变化，打开时加载问题
watch(() => props.visible, async (val) => {
  if (val && props.friend?.friend_id) {
    await loadQuestions()
  }
})

// 首次打开时也加载
onMounted(async () => {
  if (props.visible && props.friend?.friend_id) {
    await loadQuestions()
  }
})

async function loadQuestions() {
  loading.value = true
  try {
    const res = await friendApi.getCalibration(props.friend.friend_id)
    questions.value = res.data?.questions || []
    answers.value = new Array(questions.value.length).fill('')
  } catch (error) {
    console.error('Failed to load questions:', error)
    ElMessage.error('加载校准问题失败')
  } finally {
    loading.value = false
  }
}

async function handleFinalize() {
  if (answeredCount.value === 0) return

  // Save answers first
  const answerList = []
  questions.value.forEach((q, i) => {
    if (answers.value[i] && answers.value[i].trim()) {
      answerList.push({
        question: q.question,
        answer: answers.value[i].trim()
      })
    }
  })

  if (answerList.length > 0) {
    try {
      await friendApi.saveCalibration(props.friend.friend_id, answerList)
    } catch (error) {
      ElMessage.error('保存回答失败')
      return
    }
  }

  // Finalize - 触发异步生成最终人格
  finalizing.value = true
  try {
    await friendApi.finalizeFriend(props.friend.friend_id)
    // 关闭校准对话框，让父组件继续轮询状态
    emit('completed')
    ElMessage.info('正在生成最终人格，请稍候...')
  } catch (error) {
    ElMessage.error('完成校准失败，请稍后重试')
  } finally {
    finalizing.value = false
  }
}

function handleClose() {
  emit('close')
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
  padding: var(--space-6);
  overflow-y: auto;
  flex: 1;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-12);
  gap: var(--space-4);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: #8b5cf6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
}

/* Intro Section */
.intro-section {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-4);
  background: rgba(139, 92, 246, 0.06);
  border-radius: var(--border-radius-lg);
  margin-bottom: var(--space-6);
}

.intro-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
  border-radius: 50%;
  flex-shrink: 0;
}

.intro-icon svg {
  width: 20px;
  height: 20px;
}

.intro-text h4 {
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
  margin-bottom: var(--space-1);
}

.intro-text p {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  line-height: var(--leading-relaxed);
}

/* Questions List */
.questions-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.question-item {
  display: flex;
  gap: var(--space-4);
}

.question-number {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #8b5cf6;
  color: white;
  border-radius: 50%;
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  flex-shrink: 0;
}

.question-content {
  flex: 1;
}

.question-text {
  font-size: var(--text-base);
  color: var(--color-ink);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-2);
}

.question-context {
  font-size: var(--text-sm);
  color: var(--color-ink-faint);
  margin-bottom: var(--space-3);
  font-style: italic;
}

.answer-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  color: var(--color-ink);
  resize: none;
  transition: border-color var(--duration-fast), box-shadow var(--duration-fast);
}

.answer-input:focus {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.08);
}

.answer-input::placeholder {
  color: var(--color-ink-faint);
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

.footer-left {
  flex: 1;
}

.progress-text {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
}

.footer-right {
  display: flex;
  gap: var(--space-3);
}

.btn-skip {
  padding: var(--space-2) var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-ink-muted);
  transition: all var(--duration-fast);
}

.btn-skip:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-border-hover);
  color: var(--color-ink);
}

.btn-finalize {
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

.btn-finalize:hover:not(:disabled) {
  background: #7c3aed;
}

.btn-finalize:disabled {
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
