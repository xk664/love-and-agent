<template>
  <div class="app-layout" :class="layoutClass">
    <!-- ====== Desktop / Tablet Sidebar ====== -->
    <aside v-show="!isMobile" class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <span class="logo-icon">✦</span>
          <span v-show="!sidebarCollapsed" class="logo-text">AI Agent</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
        >
          <span class="nav-dot" :class="item.accent" />
          <span class="nav-icon">{{ item.icon }}</span>
          <span v-show="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <div class="avatar">{{ userInitial }}</div>
          <span v-show="!sidebarCollapsed" class="username">{{ userStore.username || '用户' }}</span>
        </div>
        <button
          v-show="!sidebarCollapsed"
          class="btn-logout"
          @click="handleLogout"
          title="退出登录"
        >
          ↗
        </button>
      </div>

      <!-- Collapse toggle (tablet only) -->
      <button v-if="isTablet" class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
        <span :class="{ rotated: sidebarCollapsed }">‹</span>
      </button>
    </aside>

    <!-- ====== Mobile Overlay ====== -->
    <Transition name="fade">
      <div
        v-if="isMobile && mobileDrawerOpen"
        class="mobile-overlay"
        @click="mobileDrawerOpen = false"
      />
    </Transition>

    <!-- ====== Mobile Drawer ====== -->
    <Transition name="slide-drawer">
      <aside v-if="isMobile && mobileDrawerOpen" class="mobile-drawer">
        <div class="drawer-header">
          <div class="logo">
            <span class="logo-icon">✦</span>
            <span class="logo-text">AI Agent</span>
          </div>
          <button class="drawer-close" @click="mobileDrawerOpen = false">✕</button>
        </div>

        <nav class="drawer-nav">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="drawer-item"
            :class="{ active: isActive(item.path) }"
            @click="mobileDrawerOpen = false"
          >
            <span class="nav-dot" :class="item.accent" />
            <span class="nav-icon">{{ item.icon }}</span>
            <span class="nav-label">{{ item.label }}</span>
          </router-link>
        </nav>

        <div class="drawer-footer">
          <div class="user-info">
            <div class="avatar">{{ userInitial }}</div>
            <span class="username">{{ userStore.username || '用户' }}</span>
          </div>
          <button class="btn-logout" @click="handleLogout">退出</button>
        </div>
      </aside>
    </Transition>

    <!-- ====== Main Area ====== -->
    <div class="main-area" :class="{ 'sidebar-open': !sidebarCollapsed && !isMobile }">
      <!-- Top Bar -->
      <header class="topbar">
        <div class="topbar-left">
          <!-- Mobile: hamburger -->
          <button v-if="isMobile" class="btn-hamburger" @click="mobileDrawerOpen = true">
            <span /><span /><span />
          </button>
          <!-- Tablet: collapse toggle -->
          <button v-else-if="isTablet" class="btn-hamburger" @click="sidebarCollapsed = !sidebarCollapsed">
            <span /><span /><span />
          </button>
          <h1 class="topbar-title">{{ pageTitle }}</h1>
        </div>
        <div class="topbar-right">
          <span class="topbar-user">{{ userStore.username || '用户' }}</span>
          <div class="topbar-avatar">{{ userInitial }}</div>
        </div>
      </header>

      <!-- Content -->
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" :key="route.path" />
          </Transition>
        </router-view>
      </main>
    </div>

    <!-- ====== Mobile Bottom Tab ====== -->
    <nav v-if="isMobile" class="bottom-tab">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="tab-item"
        :class="{ active: isActive(item.path) }"
      >
        <span class="tab-icon">{{ item.icon }}</span>
        <span class="tab-label">{{ item.label }}</span>
        <span v-if="item.accent" class="tab-dot" :class="item.accent" />
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// ---- Responsive Breakpoints ----
const windowWidth = ref(window.innerWidth)
const MOBILE_BP = 768
const TABLET_BP = 1024

const isMobile = computed(() => windowWidth.value < MOBILE_BP)
const isTablet = computed(() => windowWidth.value >= MOBILE_BP && windowWidth.value < TABLET_BP)
const isDesktop = computed(() => windowWidth.value >= TABLET_BP)

// ---- Sidebar State ----
const sidebarCollapsed = ref(false)
const mobileDrawerOpen = ref(false)

// Auto-collapse on tablet, expand on desktop
watch(windowWidth, (w) => {
  if (w < MOBILE_BP) {
    mobileDrawerOpen.value = false
  } else if (w < TABLET_BP) {
    sidebarCollapsed.value = true
  } else {
    sidebarCollapsed.value = false
  }
}, { immediate: true })

function onResize() {
  windowWidth.value = window.innerWidth
}

onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))

// ---- Layout Class ----
const layoutClass = computed(() => ({
  'is-mobile': isMobile.value,
  'is-tablet': isTablet.value,
  'is-desktop': isDesktop.value,
  'sidebar-collapsed': sidebarCollapsed.value && !isMobile.value
}))

// ---- Nav ----
const navItems = [
  { path: '/', icon: '◎', label: '首页', accent: '' },
  { path: '/love', icon: '♡', label: '恋爱大师', accent: 'coral' },
  { path: '/agent', icon: '◈', label: '超级智能体', accent: 'indigo' },
  { path: '/knowledge', icon: '☰', label: '知识库', accent: '' }
]

const pageTitle = computed(() => {
  const item = navItems.find((n) => {
    if (n.path === '/') return route.path === '/'
    return route.path.startsWith(n.path)
  })
  return item?.label || 'AI Agent'
})

const userInitial = computed(() => {
  return (userStore.username || '用').charAt(0).toUpperCase()
})

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  background: var(--color-mist);
}

/* ============================================
   DESKTOP & TABLET SIDEBAR
   ============================================ */
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-width);
  height: 100vh;
  background: var(--color-ink);
  display: flex;
  flex-direction: column;
  z-index: var(--z-sidebar);
  transition: width var(--duration-normal) var(--ease-out);
  overflow: hidden;
}

.sidebar-collapsed .sidebar {
  width: var(--sidebar-collapsed);
}

.sidebar-header {
  padding: var(--space-6) var(--space-5);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.logo-icon {
  font-size: var(--text-xl);
  color: var(--color-coral);
  flex-shrink: 0;
}

.logo-text {
  font-size: var(--text-lg);
  font-weight: var(--weight-bold);
  color: white;
  white-space: nowrap;
  letter-spacing: -0.02em;
}

/* ---- Sidebar Nav ---- */
.sidebar-nav {
  flex: 1;
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--border-radius);
  color: rgba(255, 255, 255, 0.55);
  font-size: var(--text-base);
  transition: all var(--duration-fast) var(--ease-out);
  white-space: nowrap;
}

.nav-item:hover {
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.06);
}

.nav-item.active {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.nav-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: transparent;
  flex-shrink: 0;
  transition: all var(--duration-fast);
}

.nav-dot.coral {
  background: var(--color-coral);
  box-shadow: var(--shadow-glow-coral);
}

.nav-dot.indigo {
  background: var(--color-indigo);
  box-shadow: var(--shadow-glow-indigo);
}

.nav-item.active .nav-dot:not(.coral):not(.indigo) {
  background: white;
}

.nav-icon {
  font-size: var(--text-lg);
  flex-shrink: 0;
  width: 20px;
  text-align: center;
}

.nav-label {
  flex: 1;
}

/* ---- Sidebar Footer ---- */
.sidebar-footer {
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
  min-width: 0;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--border-radius-full);
  background: var(--color-indigo);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: var(--weight-semibold);
  flex-shrink: 0;
}

.username {
  color: rgba(255, 255, 255, 0.75);
  font-size: var(--text-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.btn-logout {
  color: rgba(255, 255, 255, 0.4);
  font-size: var(--text-lg);
  padding: var(--space-1);
  border-radius: var(--border-radius);
  transition: color var(--duration-fast);
}

.btn-logout:hover {
  color: var(--color-coral);
}

.collapse-btn {
  position: absolute;
  right: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-cloud);
  box-shadow: var(--shadow-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: var(--color-stone);
  transition: all var(--duration-fast);
  z-index: 10;
}

.collapse-btn:hover {
  color: var(--color-ink);
  box-shadow: var(--shadow-lg);
}

.collapse-btn span {
  transition: transform var(--duration-normal) var(--ease-out);
}

.collapse-btn .rotated {
  transform: rotate(180deg);
}

/* ============================================
   MOBILE DRAWER
   ============================================ */
.mobile-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: calc(var(--z-sidebar) + 1);
  backdrop-filter: blur(2px);
}

.mobile-drawer {
  position: fixed;
  top: 0;
  left: 0;
  width: 280px;
  height: 100vh;
  background: var(--color-ink);
  z-index: calc(var(--z-sidebar) + 2);
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
}

.drawer-header {
  padding: var(--space-5);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.drawer-close {
  color: rgba(255, 255, 255, 0.5);
  font-size: var(--text-lg);
  padding: var(--space-1);
}

.drawer-nav {
  flex: 1;
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.drawer-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--border-radius);
  color: rgba(255, 255, 255, 0.55);
  font-size: var(--text-base);
  transition: all var(--duration-fast);
}

.drawer-item:hover,
.drawer-item.active {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.drawer-footer {
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.drawer-footer .btn-logout {
  font-size: var(--text-sm);
  color: rgba(255, 255, 255, 0.5);
}

/* ---- Drawer Transitions ---- */
.slide-drawer-enter-active,
.slide-drawer-leave-active {
  transition: transform var(--duration-normal) var(--ease-out);
}

.slide-drawer-enter-from,
.slide-drawer-leave-to {
  transform: translateX(-100%);
}

/* ============================================
   MAIN AREA
   ============================================ */
.main-area {
  min-height: 100vh;
  transition: margin-left var(--duration-normal) var(--ease-out);
}

.main-content {
  height: calc(100vh - var(--header-height));
  overflow: hidden;
  padding: 0;
}

/* Desktop: offset by sidebar width */
.is-desktop .main-area {
  margin-left: var(--sidebar-width);
}

.is-desktop.sidebar-collapsed .main-area {
  margin-left: var(--sidebar-collapsed);
}

/* Tablet: offset by collapsed sidebar */
.is-tablet .main-area {
  margin-left: var(--sidebar-collapsed);
}

.is-tablet.sidebar-collapsed .main-area {
  margin-left: var(--sidebar-collapsed);
}

/* Mobile: no offset (bottom tab handles nav) */
.is-mobile .main-area {
  margin-left: 0;
  padding-bottom: 56px; /* space for bottom tab */
}

/* ---- Top Bar ---- */
.topbar {
  position: sticky;
  top: 0;
  height: var(--header-height);
  background: rgba(248, 249, 252, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-stone-bg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  z-index: var(--z-header);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.topbar-title {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-ink);
  letter-spacing: -0.01em;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.topbar-user {
  font-size: var(--text-sm);
  color: var(--color-stone);
}

.topbar-avatar {
  width: 28px;
  height: 28px;
  border-radius: var(--border-radius-full);
  background: var(--color-indigo);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
}

/* ---- Hamburger ---- */
.btn-hamburger {
  width: 32px;
  height: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0;
}

.btn-hamburger span {
  display: block;
  width: 18px;
  height: 2px;
  background: var(--color-ink);
  border-radius: 1px;
  transition: all var(--duration-fast);
}

/* ---- Page Transition ---- */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity var(--duration-normal) var(--ease-out),
              transform var(--duration-normal) var(--ease-out);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ============================================
   MOBILE BOTTOM TAB
   ============================================ */
.bottom-tab {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: var(--color-cloud);
  border-top: 1px solid var(--color-stone-bg);
  display: flex;
  z-index: var(--z-header);
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: var(--color-stone);
  font-size: 10px;
  transition: color var(--duration-fast);
  position: relative;
}

.tab-item.active {
  color: var(--color-ink);
}

.tab-icon {
  font-size: 18px;
  line-height: 1;
}

.tab-label {
  font-weight: var(--weight-medium);
  line-height: 1;
}

.tab-dot {
  position: absolute;
  top: 4px;
  right: calc(50% - 14px);
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.tab-dot.coral {
  background: var(--color-coral);
}

.tab-dot.indigo {
  background: var(--color-indigo);
}

/* ---- Active accent on bottom tab ---- */
.tab-item.active.coral-active {
  color: var(--color-coral);
}

/* ============================================
   FADE TRANSITION (overlay)
   ============================================ */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--duration-normal) var(--ease-out);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
