<template>
  <div class="home-page">
    <!-- Hero Section -->
    <header class="hero">
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-dot" />
          <span>AI Agent System</span>
        </div>
        <h1 class="hero-title">
          <span class="title-line">智慧</span>
          <span class="title-line accent">无限可能</span>
        </h1>
        <p class="hero-desc">
          从情感陪伴到复杂任务执行，AI 超级智能体为你而生
        </p>
      </div>
      <div class="hero-decoration">
        <div class="deco-ring ring-1" />
        <div class="deco-ring ring-2" />
        <div class="deco-ring ring-3" />
      </div>
    </header>

    <!-- Features Grid -->
    <section class="features">
      <div class="feature-grid">
        <!-- Love Master -->
        <router-link to="/love" class="feature-card">
          <div class="card-icon love">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </div>
          <div class="card-content">
            <h3 class="card-title">恋爱大师</h3>
            <p class="card-desc">温暖陪伴，理解你的每一种心情</p>
          </div>
          <div class="card-arrow">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </div>
        </router-link>

        <!-- Super Agent -->
        <router-link to="/agent" class="feature-card">
          <div class="card-icon agent">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <div class="card-content">
            <h3 class="card-title">超级智能体</h3>
            <p class="card-desc">自主规划，完成复杂任务</p>
          </div>
          <div class="card-arrow">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </div>
        </router-link>

        <!-- Knowledge Base -->
        <router-link to="/knowledge" class="feature-card">
          <div class="card-icon knowledge">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
          </div>
          <div class="card-content">
            <h3 class="card-title">知识库</h3>
            <p class="card-desc">构建专属知识体系</p>
          </div>
          <div class="card-arrow">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </div>
        </router-link>

        <!-- Digital Friend -->
        <router-link to="/friend" class="feature-card">
          <div class="card-icon friend">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
          <div class="card-content">
            <h3 class="card-title">数字朋友</h3>
            <p class="card-desc">创建懂你的AI伙伴</p>
          </div>
          <div class="card-arrow">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </div>
        </router-link>
      </div>
    </section>

    <!-- Footer -->
    <footer class="home-footer">
      <p>AI 超级智能体系统 · 智慧赋能</p>
    </footer>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

/* ---- Hero ---- */
.hero {
  position: relative;
  padding: var(--space-20) var(--space-8) var(--space-16);
  text-align: center;
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 600px;
  margin: 0 auto;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-4);
  background: var(--color-accent-bg);
  border: 1px solid var(--color-accent-light);
  border-radius: var(--border-radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--color-accent-dark);
  letter-spacing: 0.5px;
  text-transform: uppercase;
  margin-bottom: var(--space-6);
  animation: fadeInDown 0.6s var(--ease-out) both;
}

.badge-dot {
  width: 6px;
  height: 6px;
  background: var(--color-accent);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.hero-title {
  font-size: clamp(2.5rem, 6vw, 4rem);
  font-weight: var(--weight-bold);
  line-height: var(--leading-tight);
  letter-spacing: -0.02em;
  margin-bottom: var(--space-5);
  animation: fadeInUp 0.7s var(--ease-out) 0.1s both;
}

.title-line {
  display: block;
  color: var(--color-ink);
}

.title-line.accent {
  background: linear-gradient(135deg, var(--color-accent-dark), var(--color-accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: var(--text-lg);
  color: var(--color-ink-muted);
  line-height: var(--leading-relaxed);
  max-width: 480px;
  margin: 0 auto;
  animation: fadeInUp 0.7s var(--ease-out) 0.2s both;
}

/* Hero Decoration */
.hero-decoration {
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

/* ---- Features ---- */
.features {
  flex: 1;
  padding: 0 var(--space-8) var(--space-12);
  max-width: var(--content-max);
  margin: 0 auto;
  width: 100%;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-5);
}

.feature-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  padding: var(--space-8);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-xl);
  transition: all var(--duration-normal) var(--ease-out);
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--card-accent, var(--color-accent)), transparent);
  opacity: 0;
  transition: opacity var(--duration-normal) var(--ease-out);
}

.feature-card:hover {
  border-color: var(--color-border-hover);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.feature-card:hover::before {
  opacity: 1;
}

.card-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius-lg);
  transition: all var(--duration-normal) var(--ease-out);
}

.card-icon svg {
  width: 24px;
  height: 24px;
}

.card-icon.love {
  background: linear-gradient(135deg, #fdf2f8, #fce7f3);
  color: #ec4899;
}

.card-icon.agent {
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  color: #3b82f6;
}

.card-icon.knowledge {
  background: linear-gradient(135deg, #f0fdf4, #dcfce7);
  color: #10b981;
}

.card-icon.friend {
  background: linear-gradient(135deg, #f5f3ff, #ede9fe);
  color: #8b5cf6;
}

.feature-card:hover .card-icon.love {
  background: linear-gradient(135deg, #fce7f3, #fbcfe8);
  box-shadow: 0 4px 12px rgba(236, 72, 153, 0.2);
}

.feature-card:hover .card-icon.agent {
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.feature-card:hover .card-icon.knowledge {
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.feature-card:hover .card-icon.friend {
  background: linear-gradient(135deg, #ede9fe, #ddd6fe);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
  margin-bottom: var(--space-2);
}

.card-desc {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  line-height: var(--leading-relaxed);
}

.card-arrow {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-ink-faint);
  transition: all var(--duration-normal) var(--ease-out);
  align-self: flex-end;
}

.card-arrow svg {
  width: 18px;
  height: 18px;
}

.feature-card:hover .card-arrow {
  color: var(--color-accent);
  transform: translateX(4px);
}

/* ---- Footer ---- */
.home-footer {
  padding: var(--space-6) var(--space-8);
  text-align: center;
  border-top: 1px solid var(--color-border-light);
}

.home-footer p {
  font-size: var(--text-xs);
  color: var(--color-ink-faint);
  letter-spacing: 0.5px;
}

/* ---- Animations ---- */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* ---- Responsive ---- */
@media (max-width: 768px) {
  .hero {
    padding: var(--space-12) var(--space-6) var(--space-10);
  }

  .hero-title {
    font-size: 2.25rem;
  }

  .features {
    padding: 0 var(--space-4) var(--space-8);
  }

  .feature-grid {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }

  .feature-card {
    padding: var(--space-6);
  }

  .deco-ring {
    display: none;
  }
}
</style>
