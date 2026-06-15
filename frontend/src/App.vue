<template>
  <div class="app-container">
    <!-- 左侧导航栏 -->
    <SidebarNav :currentRoute="currentRoute" @navigate="navigate" />
    <!-- 中间列表面板 -->
    <div class="list-panel">
      <router-view />
    </div>
    <!-- 右侧详情面板 -->
    <div class="detail-panel" v-if="showDetail">
      <router-view name="detail" />
    </div>
    <div class="detail-panel empty-detail" v-else>
      <div class="empty-state">
        <i class="fa-solid fa-user-group fa-3x"></i>
        <p>选择一个用户查看详情</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import SidebarNav from './components/SidebarNav.vue'

const router = useRouter()
const route = useRoute()

const currentRoute = computed(() => route.name)

// 当有命名视图 detail 时显示右侧面板
const showDetail = computed(() => {
  return route.matched.some(r => r.components?.detail)
})

function navigate(name) {
  router.push({ name })
}
</script>

<style>
/* ========== CSS 变量（QQ 风格主题色） ========== */
:root {
  --primary-color: #12B7F5;
  --primary-hover: #0E9FD8;
  --sidebar-bg: #2E3238;
  --panel-bg: #EBF0F5;
  --chat-bg: #F5F6FA;
  --text-dark: #1A1A1A;
  --text-gray: #8C8C8C;
  --text-light: #FFFFFF;
  --border-light: #DCDFE6;
  --danger-color: #FA5151;
  --success-color: #4CD964;
}

/* ========== 主容器：铺满视口不留白 ========== */
.app-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  background: #F5F6FA;
  overflow: hidden;
}

/* ========== 中间列表面板 ========== */
.list-panel {
  width: 320px;
  min-width: 320px;
  background: var(--panel-bg);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-light);
  overflow: hidden;
}

/* ========== 右侧详情面板 ========== */
.detail-panel {
  flex: 1;
  background: #FFFFFF;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.empty-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--chat-bg);
}

.empty-state {
  text-align: center;
  color: var(--text-gray);
}

.empty-state i {
  margin-bottom: 12px;
  display: block;
}

.empty-state p {
  font-size: 14px;
}
</style>
