<template>
  <div class="knowledge-page">
    <div class="page-header">
      <div class="header-top">
        <div>
          <h1 class="page-title">
            <span class="title-icon">☰</span>
            知识库
          </h1>
          <p class="page-subtitle">上传文档，构建专属知识体系</p>
        </div>
        <div class="header-stats" v-if="documents.length > 0">
          <span class="stat">{{ documents.length }} 份文档</span>
        </div>
      </div>
    </div>

    <div class="knowledge-content">
      <!-- Upload area -->
      <div class="upload-section">
        <div
          class="upload-zone"
          :class="{ dragover, uploading: uploadingCount > 0 }"
          @dragover.prevent="dragover = true"
          @dragleave="dragover = false"
          @drop.prevent="handleDrop"
          @click="triggerUpload"
        >
          <input
            ref="fileInput"
            type="file"
            accept=".md,.pdf,.txt"
            multiple
            hidden
            @change="handleFileChange"
          />

          <!-- Upload progress state -->
          <div v-if="uploadingCount > 0" class="upload-progress-state">
            <div class="upload-spinner" />
            <p class="upload-text">正在上传 {{ uploadingCount }} 个文件...</p>
            <div class="upload-progress-bar">
              <div class="progress-fill" :style="{ width: uploadProgress + '%' }" />
            </div>
          </div>

          <!-- Default state -->
          <template v-else>
            <div class="upload-icon-wrap">
              <svg class="upload-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <p class="upload-text">拖拽文件到此处，或点击上传</p>
            <p class="upload-hint">支持 .md / .pdf / .txt 格式，单个文件不超过 10MB</p>
          </template>
        </div>
      </div>

      <!-- Document list -->
      <div class="doc-list" v-if="documents.length > 0 || loading">
        <!-- Table header -->
        <div class="list-header">
          <span class="col-title">文档标题</span>
          <span class="col-type">类型</span>
          <span class="col-status">状态</span>
          <span class="col-time">上传时间</span>
          <span class="col-action">操作</span>
        </div>

        <!-- Loading skeleton -->
        <template v-if="loading && documents.length === 0">
          <div v-for="i in 3" :key="i" class="doc-row skeleton">
            <span class="col-title"><div class="skel-bar" /></span>
            <span class="col-type"><div class="skel-bar short" /></span>
            <span class="col-status"><div class="skel-bar short" /></span>
            <span class="col-time"><div class="skel-bar short" /></span>
            <span class="col-action"><div class="skel-bar short" /></span>
          </div>
        </template>

        <!-- Document rows -->
        <div
          v-for="doc in documents"
          :key="doc.id"
          class="doc-row"
        >
          <span class="col-title">
            <span class="file-icon" :class="getFileTypeClass(doc.fileType)">
              {{ getFileType(doc.fileType) }}
            </span>
            <span class="doc-name">{{ doc.title }}</span>
          </span>
          <span class="col-type">
            <span class="type-badge">{{ getFileType(doc.fileType) }}</span>
          </span>
          <span class="col-status">
            <span class="status-badge" :class="statusClass(doc.status)">
              <span class="status-dot" />
              {{ statusLabel(doc.status) }}
            </span>
          </span>
          <span class="col-time">
            {{ formatTime(doc.createTime || doc.create_time) }}
          </span>
          <span class="col-action">
            <button
              v-if="doc.status === 2"
              class="btn-retry"
              @click="retryDoc(doc)"
            >
              重试
            </button>
            <button
              class="btn-delete"
              @click="deleteDoc(doc)"
            >
              删除
            </button>
          </span>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="pagination">
          <button
            class="page-btn"
            :disabled="currentPage <= 1"
            @click="goPage(currentPage - 1)"
          >
            ‹
          </button>
          <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
          <button
            class="page-btn"
            :disabled="currentPage >= totalPages"
            @click="goPage(currentPage + 1)"
          >
            ›
          </button>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else-if="!loading" class="empty-state">
        <div class="empty-icon">📚</div>
        <h3>还没有文档</h3>
        <p>上传文档后，AI 可以在对话中引用这些知识来回答问题</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

const fileInput = ref(null)
const dragover = ref(false)
const documents = ref([])
const loading = ref(false)
const uploadingCount = ref(0)
const uploadProgress = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

onMounted(() => {
  fetchDocuments()
})

// ---- Fetch documents ----
async function fetchDocuments(page = 1) {
  loading.value = true
  try {
    const res = await request({
      url: '/v1/knowledge/documents',
      method: 'get',
      params: { page, page_size: pageSize.value }
    })
    const data = res.data || res
    documents.value = data.records || data.list || data.items || []
    total.value = data.total || data.pagination?.total || documents.value.length
    currentPage.value = data.current || page
  } catch {
    documents.value = []
  } finally {
    loading.value = false
  }
}

function goPage(page) {
  if (page < 1 || page > totalPages.value) return
  fetchDocuments(page)
}

// ---- Upload ----
function triggerUpload() {
  if (uploadingCount.value > 0) return
  fileInput.value?.click()
}

function handleFileChange(e) {
  const files = Array.from(e.target.files)
  if (files.length) uploadFiles(files)
  e.target.value = ''
}

function handleDrop(e) {
  dragover.value = false
  const files = Array.from(e.dataTransfer.files)
  if (files.length) uploadFiles(files)
}

async function uploadFiles(files) {
  // Validate file types
  const allowed = ['.md', '.markdown', '.pdf', '.txt']
  const valid = files.filter(f => {
    const ext = '.' + f.name.split('.').pop().toLowerCase()
    return allowed.includes(ext)
  })
  if (valid.length === 0) {
    ElMessage.warning('仅支持 .md / .pdf / .txt 格式')
    return
  }

  uploadingCount.value = valid.length
  uploadProgress.value = 0

  let success = 0
  for (let i = 0; i < valid.length; i++) {
    const file = valid[i]
    const formData = new FormData()
    formData.append('file', file)
    try {
      await request({
        url: '/v1/knowledge/document',
        method: 'post',
        data: formData,
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      success++
      ElMessage.success(`${file.name} 上传成功`)
    } catch {
      ElMessage.error(`${file.name} 上传失败`)
    }
    uploadProgress.value = Math.round(((i + 1) / valid.length) * 100)
  }

  uploadingCount.value = 0
  uploadProgress.value = 0
  if (success > 0) fetchDocuments()
}

// ---- Delete ----
async function deleteDoc(doc) {
  const title = doc.title || '该文档'
  try {
    await ElMessageBox.confirm(
      `确定删除「${title}」？删除后不可恢复。`,
      '删除文档',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    await request({
      url: `/v1/knowledge/document/${doc.id}`,
      method: 'delete'
    })
    ElMessage.success('已删除')
    fetchDocuments(currentPage.value)
  } catch {}
}

// ---- Retry ----
async function retryDoc(doc) {
  try {
    await request({
      url: `/v1/knowledge/document/${doc.id}/retry`,
      method: 'post'
    })
    ElMessage.success('已重新提交向量化')
    fetchDocuments(currentPage.value)
  } catch {}
}

// ---- Formatters ----
function getFileType(type) {
  if (!type) return '?'
  const map = { markdown: 'MD', pdf: 'PDF', txt: 'TXT' }
  return map[type.toLowerCase()] || type.split('.').pop().toUpperCase()
}

function getFileTypeClass(type) {
  if (!type) return ''
  const normalized = type.toLowerCase()
  if (normalized === 'markdown' || normalized === 'md') return 'type-md'
  if (normalized === 'pdf') return 'type-pdf'
  if (normalized === 'txt') return 'type-txt'
  return ''
}

function statusLabel(status) {
  const map = { 0: '待处理', 1: '已向量化', 2: '失败' }
  return map[status] || '未知'
}

function statusClass(status) {
  const map = { 0: 'pending', 1: 'done', 2: 'failed' }
  return map[status] || ''
}

function formatTime(time) {
  if (!time) return ''
  const d = new Date(time)
  if (isNaN(d.getTime())) return ''
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hour = d.getHours().toString().padStart(2, '0')
  const min = d.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hour}:${min}`
}
</script>

<style scoped>
.knowledge-page {
  min-height: 100vh;
  background: var(--color-mist);
}

.page-header {
  padding: var(--space-5) var(--space-6);
  background: var(--color-cloud);
  border-bottom: 1px solid var(--color-stone-bg);
}

.header-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.page-title {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.title-icon {
  font-size: var(--text-lg);
  color: var(--color-stone);
}

.page-subtitle {
  font-size: var(--text-sm);
  color: var(--color-stone);
  margin-top: var(--space-1);
}

.header-stats {
  display: flex;
  gap: var(--space-4);
}

.stat {
  font-size: var(--text-sm);
  color: var(--color-stone);
  padding: var(--space-1) var(--space-3);
  background: var(--color-stone-bg);
  border-radius: var(--border-radius-full);
}

.knowledge-content {
  max-width: 960px;
  margin: 0 auto;
  padding: var(--space-6);
}

/* ===== Upload ===== */
.upload-section {
  margin-bottom: var(--space-5);
}

.upload-zone {
  border: 2px dashed var(--color-stone-light);
  border-radius: var(--border-radius-lg);
  padding: var(--space-8);
  text-align: center;
  cursor: pointer;
  transition: all var(--duration-fast);
  background: var(--color-cloud);
}

.upload-zone:hover,
.upload-zone.dragover {
  border-color: var(--color-indigo);
  background: var(--color-indigo-bg);
}

.upload-zone.uploading {
  border-color: var(--color-indigo);
  border-style: solid;
  cursor: default;
}

.upload-icon-wrap {
  margin-bottom: var(--space-3);
}

.upload-svg {
  width: 36px;
  height: 36px;
  color: var(--color-stone);
  transition: color var(--duration-fast);
}

.upload-zone:hover .upload-svg {
  color: var(--color-indigo);
}

.upload-text {
  font-size: var(--text-base);
  color: var(--color-ink);
  margin-bottom: var(--space-1);
}

.upload-hint {
  font-size: var(--text-xs);
  color: var(--color-stone);
}

/* Upload progress */
.upload-progress-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
}

.upload-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--color-stone-bg);
  border-top-color: var(--color-indigo);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.upload-progress-bar {
  width: 200px;
  height: 4px;
  background: var(--color-stone-bg);
  border-radius: var(--border-radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-indigo);
  border-radius: var(--border-radius-full);
  transition: width var(--duration-fast);
}

/* ===== Document List ===== */
.doc-list {
  background: var(--color-cloud);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.list-header {
  display: flex;
  padding: var(--space-3) var(--space-5);
  background: var(--color-mist);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-stone);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.doc-row {
  display: flex;
  align-items: center;
  padding: var(--space-3) var(--space-5);
  border-bottom: 1px solid var(--color-stone-bg);
  transition: background var(--duration-fast);
}

.doc-row:hover:not(.skeleton) {
  background: var(--color-mist);
}

.doc-row:last-child {
  border-bottom: none;
}

.col-title {
  flex: 2.5;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}

.col-type { flex: 0.8; }
.col-status { flex: 1; }
.col-time { flex: 1; font-size: var(--text-xs); color: var(--color-stone); }
.col-action {
  flex: 1;
  display: flex;
  gap: var(--space-2);
  justify-content: flex-end;
}

.doc-name {
  font-size: var(--text-sm);
  color: var(--color-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* File type icon */
.file-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--border-radius);
  font-size: 10px;
  font-weight: var(--weight-bold);
  flex-shrink: 0;
  letter-spacing: -0.5px;
}

.file-icon.type-md {
  background: rgba(99, 102, 241, 0.1);
  color: var(--color-indigo);
}

.file-icon.type-pdf {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-danger);
}

.file-icon.type-txt {
  background: rgba(148, 163, 184, 0.15);
  color: var(--color-stone);
}

.type-badge {
  font-size: var(--text-xs);
  padding: 2px 8px;
  background: var(--color-stone-bg);
  border-radius: var(--border-radius);
  color: var(--color-ink-muted);
  font-weight: var(--weight-medium);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  padding: 2px 10px;
  border-radius: var(--border-radius-full);
  font-weight: var(--weight-medium);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-badge.pending {
  background: rgba(245, 158, 11, 0.08);
  color: var(--color-warning);
}
.status-badge.pending .status-dot { background: var(--color-warning); }

.status-badge.done {
  background: rgba(16, 185, 129, 0.08);
  color: var(--color-success);
}
.status-badge.done .status-dot { background: var(--color-success); }

.status-badge.failed {
  background: rgba(239, 68, 68, 0.08);
  color: var(--color-danger);
}
.status-badge.failed .status-dot { background: var(--color-danger); }

.btn-retry {
  font-size: var(--text-xs);
  padding: 4px 12px;
  border-radius: var(--border-radius);
  color: var(--color-indigo);
  background: var(--color-indigo-bg);
  transition: all var(--duration-fast);
}

.btn-retry:hover {
  background: var(--color-indigo);
  color: white;
}

.btn-delete {
  font-size: var(--text-xs);
  padding: 4px 12px;
  border-radius: var(--border-radius);
  color: var(--color-stone);
  transition: all var(--duration-fast);
}

.btn-delete:hover {
  color: var(--color-danger);
  background: rgba(239, 68, 68, 0.08);
}

/* ===== Pagination ===== */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-4);
  border-top: 1px solid var(--color-stone-bg);
}

.page-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--border-radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-lg);
  color: var(--color-ink-muted);
  background: var(--color-mist);
  transition: all var(--duration-fast);
}

.page-btn:hover:not(:disabled) {
  background: var(--color-indigo-bg);
  color: var(--color-indigo);
}

.page-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-info {
  font-size: var(--text-sm);
  color: var(--color-stone);
}

/* ===== Empty State ===== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-8);
  gap: var(--space-3);
}

.empty-icon {
  font-size: 48px;
  opacity: 0.4;
}

.empty-state h3 {
  font-size: var(--text-lg);
  font-weight: var(--weight-medium);
  color: var(--color-ink-muted);
}

.empty-state p {
  font-size: var(--text-sm);
  color: var(--color-stone);
  text-align: center;
  max-width: 360px;
  line-height: var(--leading-relaxed);
}

/* ===== Skeleton ===== */
.skeleton .skel-bar {
  height: 14px;
  background: var(--color-stone-bg);
  border-radius: var(--border-radius);
  animation: shimmer 1.5s infinite;
}

.skeleton .skel-bar.short {
  width: 60px;
}

@keyframes shimmer {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .knowledge-content {
    padding: var(--space-4);
  }

  .col-time,
  .col-type {
    display: none;
  }

  .doc-row,
  .list-header {
    padding: var(--space-3) var(--space-4);
  }
}
</style>
