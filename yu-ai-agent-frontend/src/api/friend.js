/**
 * Digital Friend API module.
 * Handles CRUD operations, source materials, distillation, and calibration.
 */
import request from '@/utils/request'

/**
 * Create a new digital friend
 * @param {Object} data - { name, description?, avatar_url? }
 * @returns {Promise<{friend_id: number, name: string, ...}>}
 */
export function createFriend(data) {
  return request.post('/v1/friend/create', data)
}

/**
 * List digital friends (paginated)
 * @param {Object} params - { page?, page_size? }
 * @returns {Promise<{items: Array, total: number, page: number, page_size: number}>}
 */
export function listFriends(params = {}) {
  return request.get('/v1/friend/list', { params })
}

/**
 * Get digital friend details
 * @param {number} friendId
 * @returns {Promise<Object>} - Friend details with materials
 */
export function getFriend(friendId) {
  return request.get(`/v1/friend/${friendId}`)
}

/**
 * Update digital friend info
 * @param {number} friendId
 * @param {Object} data - { name?, description?, avatar_url? }
 */
export function updateFriend(friendId, data) {
  return request.put(`/v1/friend/${friendId}`, data)
}

/**
 * Delete a digital friend
 * @param {number} friendId
 */
export function deleteFriend(friendId) {
  return request.delete(`/v1/friend/${friendId}`)
}

/**
 * Add source materials to a friend
 * @param {number} friendId
 * @param {Array<Object>} materials - [{ type: 'chat_log'|'moments'|'hobby'|'habit'|'description', content: string }]
 */
export function addSource(friendId, materials) {
  return request.post(`/v1/friend/${friendId}/source`, { materials })
}

/**
 * Upload file as source material
 * @param {number} friendId
 * @param {File} file - .txt, .csv, .md file
 * @param {Object} options - { source_type?, title? }
 * @returns {Promise<Object>}
 */
export function uploadSourceFile(friendId, file, options = {}) {
  const formData = new FormData()
  formData.append('file', file)
  if (options.source_type) {
    formData.append('source_type', options.source_type)
  }
  if (options.title) {
    formData.append('title', options.title)
  }
  return request.post(`/v1/friend/${friendId}/source/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * Trigger personality distillation (generate system prompt from materials)
 * @param {number} friendId
 * @returns {Promise<Object>} - { task_id, status }
 */
export function distillFriend(friendId) {
  return request.post(`/v1/friend/${friendId}/distill`)
}

/**
 * Get distillation status
 * @param {number} friendId
 * @returns {Promise<Object>} - { status: 'pending'|'processing'|'completed'|'failed', progress? }
 */
export function getFriendStatus(friendId) {
  return request.get(`/v1/friend/${friendId}/status`)
}

/**
 * Get calibration questions (after distillation)
 * @param {number} friendId
 * @returns {Promise<Object>} - { questions: [{ id, question, context? }] }
 */
export function getCalibration(friendId) {
  return request.get(`/v1/friend/${friendId}/calibration`)
}

/**
 * Save calibration answers
 * @param {number} friendId
 * @param {Array<Object>} answers - [{ question: string, answer: string }]
 */
export function saveCalibration(friendId, answers) {
  return request.post(`/v1/friend/${friendId}/calibration`, { answers })
}

/**
 * Finalize calibration and generate final personality
 * @param {number} friendId
 * @returns {Promise<Object>} - { success, system_prompt? }
 */
export function finalizeFriend(friendId) {
  return request.post(`/v1/friend/${friendId}/finalize`)
}
