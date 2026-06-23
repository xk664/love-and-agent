<template>
  <div class="home-page">
    <div class="home-hero">
      <h1 class="hero-title">
        <span class="hero-accent">✦</span>
        AI 超级智能体
      </h1>
      <p class="hero-subtitle">温暖陪伴，智慧赋能</p>
    </div>

    <div class="feature-grid">
      <router-link to="/love" class="feature-card feature-coral">
        <div class="feature-icon">♡</div>
        <h3 class="feature-name">恋爱大师</h3>
        <p class="feature-desc">情感陪伴与恋爱指导，用温暖的方式理解你的每一种心情</p>
        <span class="feature-arrow">→</span>
      </router-link>

      <router-link to="/agent" class="feature-card feature-indigo">
        <div class="feature-icon">◈</div>
        <h3 class="feature-name">超级智能体</h3>
        <p class="feature-desc">自主规划、多步推理，帮你完成复杂任务</p>
        <span class="feature-arrow">→</span>
      </router-link>

      <router-link to="/knowledge" class="feature-card feature-neutral">
        <div class="feature-icon">☰</div>
        <h3 class="feature-name">知识库</h3>
        <p class="feature-desc">上传文档，构建专属知识体系，让 AI 更懂你</p>
        <span class="feature-arrow">→</span>
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  padding: var(--space-12) var(--space-8);
  max-width: var(--content-max);
  margin: 0 auto;
}

.home-hero {
  text-align: center;
  padding: var(--space-16) 0 var(--space-12);
}

.hero-title {
  font-size: var(--text-3xl);
  font-weight: var(--weight-bold);
  color: var(--color-ink);
  letter-spacing: -0.03em;
  line-height: var(--leading-tight);
}

.hero-accent {
  color: var(--color-coral);
  margin-right: var(--space-2);
}

.hero-subtitle {
  margin-top: var(--space-4);
  font-size: var(--text-lg);
  color: var(--color-stone);
  letter-spacing: 0.1em;
}

/* ---- Feature Grid ---- */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-6);
  margin-top: var(--space-8);
}

.feature-card {
  background: var(--color-cloud);
  border-radius: var(--border-radius-lg);
  padding: var(--space-8);
  position: relative;
  overflow: hidden;
  transition: all var(--duration-normal) var(--ease-out);
  border: 1px solid transparent;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.feature-coral:hover {
  border-color: var(--color-coral-light);
  box-shadow: var(--shadow-lg), var(--shadow-glow-coral);
}

.feature-indigo:hover {
  border-color: var(--color-indigo-light);
  box-shadow: var(--shadow-lg), var(--shadow-glow-indigo);
}

.feature-neutral:hover {
  border-color: var(--color-stone-light);
}

.feature-icon {
  font-size: var(--text-2xl);
  margin-bottom: var(--space-2);
}

.feature-coral .feature-icon { color: var(--color-coral); }
.feature-indigo .feature-icon { color: var(--color-indigo); }
.feature-neutral .feature-icon { color: var(--color-stone); }

.feature-name {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
}

.feature-desc {
  font-size: var(--text-base);
  color: var(--color-stone);
  line-height: var(--leading-relaxed);
  flex: 1;
}

.feature-arrow {
  font-size: var(--text-xl);
  color: var(--color-stone-light);
  transition: transform var(--duration-fast) var(--ease-out);
  align-self: flex-end;
}

.feature-card:hover .feature-arrow {
  transform: translateX(4px);
}

.feature-coral:hover .feature-arrow { color: var(--color-coral); }
.feature-indigo:hover .feature-arrow { color: var(--color-indigo); }
</style>
