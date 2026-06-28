/**
 * Chat API module.
 * Handles SSE streaming for real-time AI responses.
 */
import { connectSSE, createSSEController } from '@/utils/sse'

const BASE = import.meta.env.VITE_API_BASE || '/api'

/**
 * Send a message via SSE streaming.
 *
 * The backend returns Server-Sent Events with these types:
 * - thinking: AI is processing (content: "正在思考...")
 * - answer:   streaming text chunk (content: sentence fragment)
 * - metadata: end-of-stream stats (content: { tokens_used, model, rag_sources })
 * - error:    error message (message: error string)
 * - [DONE]:   terminal marker
 *
 * @param {Object} params
 * @param {string} params.chat_id - Chat session ID
 * @param {string} params.message - User message text
 * @param {Object} callbacks
 * @param {Function} callbacks.onThinking - Called when AI starts thinking
 * @param {Function} callbacks.onAnswer - Called with each text chunk: (content) => void
 * @param {Function} callbacks.onMetadata - Called with end-of-stream metadata: (metadata) => void
 * @param {Function} callbacks.onError - Called on error: (errorMsg) => void
 * @param {Function} callbacks.onDone - Called when stream completes
 * @returns {{ cancel: () => void }} - Cancel function to abort the stream
 */
export function sendMessageStream({ chat_id, message }, { onThinking, onAnswer, onMetadata, onError, onDone }) {
  const { controller, cancel } = createSSEController()

  connectSSE(
    `${BASE}/v1/ai/love/chat/sse`,
    { chat_id, message },
    {
      signal: controller.signal,
      onEvent(type, data) {
        switch (type) {
          case 'thinking':
            onThinking?.(data.content)
            break
          case 'answer':
            onAnswer?.(data.content)
            break
          case 'metadata':
            onMetadata?.(data.content)
            break
          case 'error':
            onError?.(data.message || '请求失败')
            break
        }
      },
      onDone() {
        onDone?.()
      },
      onError(err) {
        onError?.(err.message || '网络异常')
      }
    }
  )

  return { cancel }
}
