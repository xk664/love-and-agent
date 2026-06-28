<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo -->
      <div class="login-header">
        <div class="logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
        </div>
        <h1 class="login-title">AI 超级智能体</h1>
        <p class="login-subtitle">{{ isRegister ? '创建账号' : '欢迎回来' }}</p>
      </div>

      <!-- Form -->
      <form class="login-form" @submit.prevent="handleSubmit">
        <!-- Username -->
        <div class="form-field" :class="{ error: fieldErrors.username }">
          <label class="field-label">用户名</label>
          <input
            v-model="form.username"
            type="text"
            placeholder="请输入用户名"
            autocomplete="username"
            @blur="validateField('username')"
            @input="clearError('username')"
          />
          <span v-if="fieldErrors.username" class="field-hint">{{ fieldErrors.username }}</span>
        </div>

        <!-- Password -->
        <div class="form-field" :class="{ error: fieldErrors.password }">
          <label class="field-label">密码</label>
          <input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :autocomplete="isRegister ? 'new-password' : 'current-password'"
            @blur="validateField('password')"
            @input="clearError('password')"
          />
          <span v-if="fieldErrors.password" class="field-hint">{{ fieldErrors.password }}</span>
        </div>

        <!-- Confirm Password (register only) -->
        <div v-if="isRegister" class="form-field" :class="{ error: fieldErrors.confirmPassword }">
          <label class="field-label">确认密码</label>
          <input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            autocomplete="new-password"
            @blur="validateField('confirmPassword')"
            @input="clearError('confirmPassword')"
          />
          <span v-if="fieldErrors.confirmPassword" class="field-hint">{{ fieldErrors.confirmPassword }}</span>
        </div>

        <!-- Error/Success messages -->
        <p v-if="globalError" class="form-message error">{{ globalError }}</p>
        <p v-if="registerSuccess" class="form-message success">注册成功，请登录</p>

        <!-- Submit button -->
        <button type="submit" class="btn-submit" :disabled="loading">
          <span v-if="loading" class="btn-loading" />
          <span v-else>{{ isRegister ? '注册' : '登录' }}</span>
        </button>
      </form>

      <!-- Toggle mode -->
      <p class="login-switch">
        {{ isRegister ? '已有账号？' : '没有账号？' }}
        <a href="#" @click.prevent="toggleMode">
          {{ isRegister ? '去登录' : '去注册' }}
        </a>
      </p>
    </div>

    <!-- Background decoration -->
    <div class="bg-decoration">
      <div class="deco-ring ring-1" />
      <div class="deco-ring ring-2" />
      <div class="deco-ring ring-3" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const isRegister = ref(false)
const loading = ref(false)
const globalError = ref('')
const registerSuccess = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const fieldErrors = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

// ---- Validation Rules ----
const rules = {
  username: [
    { test: (v) => v.trim().length > 0, msg: '请输入用户名' }
  ],
  password: [
    { test: (v) => v.length > 0, msg: '请输入密码' }
  ],
  confirmPassword: [
    { test: (v) => v.length > 0, msg: '请确认密码' },
    { test: (v) => v === form.password, msg: '两次密码输入不一致' }
  ]
}

function validateField(field) {
  const fieldRules = rules[field]
  if (!fieldRules) return true
  for (const rule of fieldRules) {
    if (!rule.test(form[field])) {
      fieldErrors[field] = rule.msg
      return false
    }
  }
  fieldErrors[field] = ''
  return true
}

function clearError(field) {
  fieldErrors[field] = ''
  globalError.value = ''
}

function validateAll() {
  const fields = isRegister.value
    ? ['username', 'password', 'confirmPassword']
    : ['username', 'password']
  let valid = true
  for (const field of fields) {
    if (!validateField(field)) valid = false
  }
  return valid
}

function toggleMode() {
  isRegister.value = !isRegister.value
  globalError.value = ''
  registerSuccess.value = false
  fieldErrors.username = ''
  fieldErrors.password = ''
  fieldErrors.confirmPassword = ''
  form.password = ''
  form.confirmPassword = ''
}

// ---- Submit ----
async function handleSubmit() {
  globalError.value = ''
  registerSuccess.value = false

  if (!validateAll()) return

  loading.value = true
  try {
    if (isRegister.value) {
      await userStore.register(form.username.trim(), form.password)
      registerSuccess.value = true
      isRegister.value = false
      form.password = ''
      form.confirmPassword = ''
      return
    }
    await userStore.login(form.username.trim(), form.password)
    router.push('/')
  } catch (e) {
    globalError.value = e.message || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  padding: var(--space-6);
  position: relative;
  overflow: hidden;
}

.login-card {
  width: 100%;
  max-width: 380px;
  background: var(--color-surface);
  border-radius: var(--border-radius-xl);
  padding: var(--space-10) var(--space-8);
  border: 1px solid var(--color-border);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: var(--space-8);
}

.logo {
  width: 56px;
  height: 56px;
  margin: 0 auto var(--space-4);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: white;
  border-radius: var(--border-radius-lg);
}

.logo svg {
  width: 28px;
  height: 28px;
}

.login-title {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  color: var(--color-ink);
  letter-spacing: -0.02em;
}

.login-subtitle {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  margin-top: var(--space-2);
}

/* ---- Form ---- */
.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.field-label {
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-ink-muted);
}

.form-field input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius);
  font-size: var(--text-base);
  transition: all var(--duration-fast);
  background: var(--color-bg);
  color: var(--color-ink);
}

.form-field input::placeholder {
  color: var(--color-ink-faint);
}

.form-field input:focus {
  border-color: var(--color-accent);
  background: var(--color-surface);
  box-shadow: 0 0 0 3px var(--color-accent-bg);
}

.form-field.error input {
  border-color: var(--color-danger);
  background: var(--color-danger-bg);
}

.form-field.error input:focus {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.field-hint {
  font-size: var(--text-xs);
  color: var(--color-danger);
  padding-left: var(--space-1);
}

.form-message {
  font-size: var(--text-sm);
  text-align: center;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--border-radius);
}

.form-message.error {
  color: var(--color-danger);
  background: var(--color-danger-bg);
}

.form-message.success {
  color: var(--color-success);
  background: var(--color-success-bg);
}

.btn-submit {
  width: 100%;
  padding: var(--space-3);
  background: var(--color-primary);
  color: white;
  border-radius: var(--border-radius);
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  transition: all var(--duration-fast);
  margin-top: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
}

.btn-submit:hover:not(:disabled) {
  background: var(--color-primary-light);
  transform: translateY(-1px);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-loading {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.login-switch {
  text-align: center;
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  margin-top: var(--space-6);
}

.login-switch a {
  color: var(--color-accent-dark);
  font-weight: var(--weight-medium);
}

.login-switch a:hover {
  text-decoration: underline;
}

/* ---- Background Decoration ---- */
.bg-decoration {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.deco-ring {
  position: absolute;
  border: 1px solid var(--color-border-light);
  border-radius: 50%;
  transform: translate(-50%, -50%);
}

.ring-1 {
  width: 300px;
  height: 300px;
  animation: ringPulse 4s ease-in-out infinite;
}

.ring-2 {
  width: 450px;
  height: 450px;
  animation: ringPulse 4s ease-in-out 0.5s infinite;
  opacity: 0.6;
}

.ring-3 {
  width: 600px;
  height: 600px;
  animation: ringPulse 4s ease-in-out 1s infinite;
  opacity: 0.3;
}

@keyframes ringPulse {
  0%, 100% {
    transform: translate(-50%, -50%) scale(1);
    opacity: var(--ring-opacity, 0.5);
  }
  50% {
    transform: translate(-50%, -50%) scale(1.05);
    opacity: calc(var(--ring-opacity, 0.5) * 0.6);
  }
}

.ring-1 { --ring-opacity: 0.5; }
.ring-2 { --ring-opacity: 0.3; }
.ring-3 { --ring-opacity: 0.15; }

@media (max-width: 480px) {
  .login-card {
    padding: var(--space-8) var(--space-6);
  }

  .deco-ring {
    display: none;
  }
}
</style>
