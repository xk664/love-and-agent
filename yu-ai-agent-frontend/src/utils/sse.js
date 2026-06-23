/**
 * SSE client for streaming chat responses.
 * Uses fetch + ReadableStream since the backend requires POST with body
 * (native EventSource only supports GET).
 */

/**
 * Connect to an SSE endpoint and consume streaming events.
 *
 * @param {string} url - The SSE endpoint URL
 * @param {Object} body - Request body (will be JSON-stringified)
 * @param {Object} options
 * @param {Function} options.onEvent - Called for each parsed event: (eventType, data) => void
 * @param {Function} options.onDone - Called when the stream ends
 * @param {Function} options.onError - Called on error: (error) => void
 * @param {AbortSignal} [options.signal] - AbortSignal to cancel the request
 * @returns {Promise<void>}
 */
export async function connectSSE(url, body, { onEvent, onDone, onError, signal }) {
  const token = (localStorage.getItem('token') || '').trim()

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        ...(token ? { Authorization: token } : {})
      },
      body: JSON.stringify(body),
      signal
    })

    if (!response.ok) {
      const text = await response.text().catch(() => '')
      let msg = `HTTP ${response.status}`
      try {
        const parsed = JSON.parse(text)
        msg = parsed.message || msg
      } catch {}
      throw new Error(msg)
    }

    // Verify we got a readable stream
    if (!response.body) {
      throw new Error('Response body is null — streaming not supported')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let eventCount = 0

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed) continue

        // Skip SSE comment lines
        if (trimmed.startsWith(':')) continue

        // Skip event name lines (we use the data payload's type field)
        if (trimmed.startsWith('event:')) continue

        // Parse data lines
        if (trimmed.startsWith('data:')) {
          const dataStr = trimmed.slice(5).trim()

          // Terminal marker
          if (dataStr === '[DONE]') {
            console.debug('[SSE] Stream complete, total events:', eventCount)
            onDone?.()
            return
          }

          try {
            const parsed = JSON.parse(dataStr)
            const eventType = parsed.type || 'message'
            eventCount++
            console.debug(`[SSE] Event #${eventCount}:`, eventType, parsed.content?.slice?.(0, 50) || parsed.content)
            onEvent?.(eventType, parsed)
          } catch (e) {
            console.warn('[SSE] Failed to parse data line:', dataStr.slice(0, 100))
          }
        }
      }
    }

    // Stream ended without [DONE]
    console.debug('[SSE] Stream ended without [DONE], total events:', eventCount)
    onDone?.()
  } catch (err) {
    if (err.name === 'AbortError') {
      console.debug('[SSE] Stream aborted')
      return
    }
    console.error('[SSE] Error:', err.message)
    onError?.(err)
  }
}

/**
 * Create an AbortController pair for cancelling SSE streams.
 * @returns {{ controller: AbortController, cancel: () => void }}
 */
export function createSSEController() {
  const controller = new AbortController()
  return {
    controller,
    cancel: () => controller.abort()
  }
}
