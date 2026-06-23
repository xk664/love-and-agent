import { defineStore } from 'pinia'
import request from '@/utils/request'
import { sendMessageStream } from '@/api/chat'

export const useChatStore = defineStore('chat', {
  state: () => ({
    // Session list
    sessions: [],
    currentChatId: null,
    currentSession: null,
    // Messages
    messages: [],
    loading: false,
    // Pagination
    page: 1,
    pageSize: 20,
    hasMore: true,
    // SSE streaming state
    streaming: false,
    thinkingContent: '',
    streamingContent: '',
    currentMetadata: null,
    // Internal (non-reactive refs managed manually)
    _cancelStream: null,
    _charQueue: [],
    _typewriterTimer: null,
    _streamFullContent: '',
    _streamDone: false,
    _streamResolve: null
  }),

  getters: {
    hasSessions: (state) => state.sessions.length > 0,
    currentMessages: (state) => state.messages,
    isStreaming: (state) => state.streaming
  },

  actions: {
    /**
     * Fetch sessions with pagination.
     * @param {Object} params - Query params (app_type, page, page_size)
     * @param {boolean} append - If true, append to existing list (load more)
     */
    async fetchSessions(params = {}, append = false) {
      this.loading = true
      try {
        const page = params.page || 1
        const res = await request({
          url: '/v1/chat/list',
          method: 'get',
          params: { page, page_size: this.pageSize, ...params }
        })
        const list = res.data?.list || res.list || []
        if (append) {
          this.sessions.push(...list)
        } else {
          this.sessions = list
        }
        this.page = page
        this.hasMore = list.length >= this.pageSize
      } finally {
        this.loading = false
      }
    },

    /**
     * Load next page of sessions.
     */
    async loadMore(params = {}) {
      if (!this.hasMore || this.loading) return
      await this.fetchSessions({ ...params, page: this.page + 1 }, true)
    },

    /**
     * Create a new session.
     */
    async createSession(data) {
      const res = await request({
        url: '/v1/chat/create',
        method: 'post',
        data
      })
      const session = res.data || res
      this.sessions.unshift(session)
      this.currentChatId = session.chatId || session.chat_id
      this.currentSession = session
      return session
    },

    /**
     * Delete a session.
     */
    async deleteSession(chatId) {
      await request({
        url: `/v1/chat/${chatId}`,
        method: 'delete'
      })
      this.sessions = this.sessions.filter(
        (s) => (s.chatId || s.chat_id) !== chatId
      )
      if (this.currentChatId === chatId) {
        this.currentChatId = null
        this.currentSession = null
        this.messages = []
      }
    },

    /**
     * Fetch messages for a session.
     */
    async fetchMessages(chatId, params = {}) {
      this.loading = true
      try {
        const res = await request({
          url: `/v1/chat/${chatId}/messages`,
          method: 'get',
          params: { page: 1, page_size: 50, ...params }
        })
        // Backend returns newest-first; reverse for chronological display
        const list = res.data?.list || res.list || []
        this.messages = list.reverse()
        this.currentChatId = chatId
      } finally {
        this.loading = false
      }
    },

    /**
     * Send a message via SSE streaming.
     * Uses a typewriter effect to display content smoothly even when
     * the backend sends tokens in bursts rather than one-by-one.
     *
     * @param {string} text - User message text
     * @returns {Promise<void>}
     */
    async sendMessage(text) {
      if (!text.trim() || !this.currentChatId || this.streaming) return

      const chatId = this.currentChatId

      // Add user message to the list
      this.messages.push({
        role: 'user',
        content: text,
        createTime: new Date().toISOString()
      })

      // Start streaming state
      this.streaming = true
      this.thinkingContent = ''
      this.streamingContent = ''
      this.currentMetadata = null
      this._charQueue = []
      this._streamFullContent = ''
      this._streamDone = false
      this._streamResolve = null

      return new Promise((resolve) => {
        this._streamResolve = resolve

        const { cancel } = sendMessageStream(
          { chatId, message: text },
          {
            onThinking: (content) => {
              this.thinkingContent = content
            },
            onAnswer: (content) => {
              // Clear thinking once we start receiving answers
              if (this.thinkingContent) {
                this.thinkingContent = ''
              }
              // Buffer characters for typewriter effect
              this._streamFullContent += content
              for (const ch of content) {
                this._charQueue.push(ch)
              }
              this._startTypewriter()
            },
            onMetadata: (metadata) => {
              this.currentMetadata = metadata
            },
            onError: (msg) => {
              this._streamDone = true
              // If we have partial content, let typewriter finish it
              if (!this._streamFullContent) {
                this.messages.push({
                  role: 'assistant',
                  content: `抱歉，发生了错误：${msg}`,
                  metadata: null,
                  isError: true,
                  createTime: new Date().toISOString()
                })
                this._resetStreamState()
                resolve()
              }
              // else: typewriter will finish remaining chars, then commit
            },
            onDone: () => {
              this._streamDone = true
              // If typewriter has nothing left, commit immediately
              if (this._charQueue.length === 0) {
                this._commitMessage()
                resolve()
              }
              // else: typewriter drains remaining chars, then calls _commitMessage
            }
          }
        )

        this._cancelStream = cancel
      })
    },

    /**
     * Start the typewriter timer.
     * Pulls characters from the queue and appends to streamingContent.
     * ~40 chars/sec feels natural for Chinese text.
     */
    _startTypewriter() {
      if (this._typewriterTimer) return

      const CHARS_PER_TICK = 2
      const TICK_MS = 25

      this._typewriterTimer = setInterval(() => {
        if (this._charQueue.length === 0) {
          // Queue empty — stop timer
          clearInterval(this._typewriterTimer)
          this._typewriterTimer = null

          // If SSE is done, commit the message
          if (this._streamDone) {
            this._commitMessage()
            this._streamResolve?.()
          }
          return
        }

        // Pull characters from queue
        let count = Math.min(CHARS_PER_TICK, this._charQueue.length)
        while (count-- > 0) {
          this.streamingContent += this._charQueue.shift()
        }
      }, TICK_MS)
    },

    /**
     * Stop the typewriter timer and flush remaining characters.
     */
    _stopTypewriter() {
      if (this._typewriterTimer) {
        clearInterval(this._typewriterTimer)
        this._typewriterTimer = null
      }
      // Flush remaining characters instantly
      if (this._charQueue.length > 0) {
        this.streamingContent += this._charQueue.join('')
        this._charQueue = []
      }
    },

    /**
     * Commit the streamed content as a complete message.
     */
    _commitMessage() {
      const content = this._streamFullContent || this.streamingContent
      if (content) {
        this.messages.push({
          role: 'assistant',
          content,
          metadata: this.currentMetadata,
          createTime: new Date().toISOString()
        })
      }
      this._resetStreamState()
    },

    /**
     * Cancel the current SSE stream.
     */
    cancelStream() {
      if (this._cancelStream) {
        this._cancelStream()
        this._streamDone = true
        this._stopTypewriter()
        this._commitMessage()
        this._streamResolve?.()
      }
    },

    /**
     * Reset streaming state (internal helper).
     */
    _resetStreamState() {
      this.streaming = false
      this.thinkingContent = ''
      this.streamingContent = ''
      this.currentMetadata = null
      this._cancelStream = null
      this._charQueue = []
      this._streamFullContent = ''
      this._streamDone = false
      this._streamResolve = null
      if (this._typewriterTimer) {
        clearInterval(this._typewriterTimer)
        this._typewriterTimer = null
      }
    },

    setCurrentSession(session) {
      this.currentSession = session
      this.currentChatId = session?.chatId || session?.chat_id || null
    },

    addMessage(message) {
      this.messages.push(message)
    },

    clearMessages() {
      this.messages = []
    },

    resetPagination() {
      this.page = 1
      this.hasMore = true
    }
  }
})
