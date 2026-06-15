<template>
  <div class="messages-view">
    <div class="list-header">
      <h3>消息</h3>
    </div>

    <!-- 会话列表 -->
    <div class="conversation-list" v-if="conversations.length > 0">
      <div
        v-for="conv in conversations"
        :key="conv.user.id"
        class="conversation-item"
        :class="{ selected: selectedUserId === conv.user.id }"
        @click="openChat(conv.user.id)"
      >
        <img :src="conv.user.avatar_url || defaultAvatar" alt="头像" class="conv-avatar" />
        <div class="conv-info">
          <div class="conv-top">
            <span class="conv-name">{{ conv.user.nickname || conv.user.username }}</span>
            <span class="conv-time">{{ formatTime(conv.updated_at) }}</span>
          </div>
          <div class="conv-bottom">
            <span class="conv-preview">{{ conv.last_message }}</span>
            <span class="unread-badge" v-if="conv.unread_count > 0">{{ conv.unread_count }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-list" v-else>
      <i class="fa-solid fa-comments fa-2x"></i>
      <p>暂无消息</p>
      <span class="empty-hint">与好友发送消息后，会话会显示在这里</span>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="total > pageSize">
      <button :disabled="page <= 1" @click="changePage(-1)">上一页</button>
      <span>{{ page }} / {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="changePage(1)">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getConversations } from '../api/index.js'

const route = useRoute()
const router = useRouter()
const MY_ID = 1

const conversations = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const selectedUserId = ref(null)

const defaultAvatar = 'https://picsum.photos/seed/default/100/100'

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
  return date.toLocaleDateString('zh-CN')
}

function changePage(delta) {
  page.value += delta
  loadConversations()
}

function openChat(userId) {
  selectedUserId.value = userId
  router.push({ name: 'Messages', params: { userId } })
}

async function loadConversations() {
  try {
    const res = await getConversations(MY_ID, {
      page: page.value,
      page_size: pageSize.value,
    })
    conversations.value = res.items
    total.value = res.total
  } catch (e) {
    console.error('加载会话列表失败:', e)
  }
}

// 监听路由参数变化，更新选中状态
watch(() => route.params.userId, (newId) => {
  selectedUserId.value = newId ? Number(newId) : null
})

onMounted(() => {
  if (route.params.userId) {
    selectedUserId.value = Number(route.params.userId)
  }
  loadConversations()
})
</script>

<style scoped>
.messages-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.list-header {
  padding: 16px 16px 8px;
}

.list-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-dark);
}

/* 会话列表 */
.conversation-list {
  flex: 1;
  overflow-y: auto;
}

.conversation-item {
  display: flex;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
  align-items: center;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.conversation-item:hover {
  background: rgba(255, 255, 255, 0.6);
}

.conversation-item.selected {
  background: rgba(18, 183, 245, 0.08);
}

.conv-avatar {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  margin-right: 12px;
  object-fit: cover;
  background: #e0e0e0;
}

.conv-info {
  flex: 1;
  overflow: hidden;
  min-width: 0;
}

.conv-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3px;
}

.conv-name {
  font-size: 14px;
  color: var(--text-dark);
  font-weight: 500;
}

.conv-time {
  font-size: 11px;
  color: var(--text-gray);
  white-space: nowrap;
  margin-left: 8px;
}

.conv-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.conv-preview {
  font-size: 12px;
  color: var(--text-gray);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.unread-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: var(--danger-color);
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  margin-left: 8px;
  flex-shrink: 0;
}

/* 空状态 */
.empty-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-gray);
  gap: 8px;
}

.empty-list p {
  font-size: 14px;
  font-weight: 500;
}

.empty-hint {
  font-size: 12px;
  color: var(--text-gray);
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 10px;
  border-top: 1px solid var(--border-light);
  font-size: 12px;
}

.pagination button {
  padding: 4px 12px;
  border: 1px solid var(--border-light);
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
}

.pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
