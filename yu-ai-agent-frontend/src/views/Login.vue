<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <span class="login-logo">✦</span>
        <h1 class="login-title">AI 超级智能体</h1>
        <p class="login-subtitle">{{ isRegister ? '创建账号' : '欢迎回来' }}</p>
      </div>

      <form class="login-form" @submit.prevent="handleSubmit">
        <!-- 用户名 -->
        <div class="form-field" :class="{ error: fieldErrors.username }">
          <input
            v-model="form.username"
            type="text"
            placeholder="用户名"
            autocomplete="username"
            @blur="validateField('username')"
            @input="clearError('username')"
          />
          <span v-if="fieldErrors.username" class="field-hint">{{ fieldErrors.username }}</span>
        </div>

        <!-- 密码 -->
        <div class="form-field" :class="{ error: fieldErrors.password }">
          <input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :autocomplete="isRegister ? 'new-password' : 'current-password'"
            @blur="validateField('password')"
            @input="clearError('password')"
          />
          <span v-if="fieldErrors.password" class="field-hint">{{ fieldErrors.password }}</span>
        </div>

        <!-- 确认密码（仅注册） -->
        <div v-if="isRegister" class="form-field" :class="{ error: fieldErrors.confirmPassword }">
          <input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            autocomplete="new-password"
            @blur="validateField('confirmPassword')"
            @input="clearError('confirmPassword')"
          />
          <span v-if="fieldErrors.confirmPassword" class="field-hint">{{ fieldErrors.confirmPassword }}</span>
        </div>

        <!-- 全局错误 -->
        <p v-if="globalError" class="form-error">{{ globalError }}</p>

        <!-- 注册成功提示 -->
        <p v-if="registerSuccess" class="form-success">注册成功，请登录</p>

        <button type="submit" class="btn-submit" :disabled="loading">
          <span v-if="loading" class="btn-loading" />
          {{ loading ? '' : (isRegister ? '注册' : '登录') }}
        </button>
      </form>

      <p class="login-switch">
        {{ isRegister ? '已有账号？' : '没有账号？' }}
        <a href="#" @click.prevent="toggleMode">
          {{ isRegister ? '去登录' : '去注册' }}
        </a>
      </p>
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
  background: var(--color-mist);
  padding: var(--space-6);
}

.login-card {
  width: 100%;
  max-width: 380px;
  background: var(--color-cloud);
  border-radius: var(--border-radius-xl);
  padding: var(--space-10) var(--space-8);
  box-shadow: var(--shadow-lg);
}

.login-header {
  text-align: center;
  margin-bottom: var(--space-8);
}

.login-logo {
  font-size: 32px;
  color: var(--color-coral);
}

.login-title {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  color: var(--color-ink);
  margin-top: var(--space-3);
  letter-spacing: -0.02em;
}

.login-subtitle {
  font-size: var(--text-sm);
  color: var(--color-stone);
  margin-top: var(--space-2);
}

/* ---- Form ---- */
.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-field {
  position: relative;
}

.form-field input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-stone-light);
  border-radius: var(--border-radius);
  font-size: var(--text-base);
  transition: all var(--duration-fast);
  background: var(--color-mist);
}

.form-field input:focus {
  border-color: var(--color-indigo);
  background: var(--color-cloud);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-field.error input {
  border-color: var(--color-danger);
  background: rgba(239, 68, 68, 0.04);
}

.form-field.error input:focus {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.field-hint {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-danger);
  margin-top: var(--space-1);
  padding-left: var(--space-1);
}

.form-error {
  font-size: var(--text-sm);
  color: var(--color-danger);
  text-align: center;
  padding: var(--space-2) var(--space-3);
  background: rgba(239, 68, 68, 0.06);
  border-radius: var(--border-radius);
}

.form-success {
  font-size: var(--text-sm);
  color: var(--color-success);
  text-align: center;
  padding: var(--space-2) var(--space-3);
  background: rgba(16, 185, 129, 0.06);
  border-radius: var(--border-radius);
}

.btn-submit {
  width: 100%;
  padding: var(--space-3);
  background: var(--color-ink);
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
  background: var(--color-ink-light);
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
  color: var(--color-stone);
  margin-top: var(--space-6);
}

.login-switch a {
  color: var(--color-indigo);
  font-weight: var(--weight-medium);
}

.login-switch a:hover {
  text-decoration: underline;
}
</style>
