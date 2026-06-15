<template>
  <div class="chat-view">
    <!-- 空状态：未选择会话 -->
    <div class="chat-empty" v-if="!userId">
      <i class="fa-solid fa-comment-dots fa-3x"></i>
      <p>选择一条消息开始聊天</p>
      <span class="empty-sub">从左侧选择一个会话查看聊天记录</span>
    </div>

    <!-- 聊天详情 -->
    <template v-else>
      <!-- 顶部 header -->
      <div class="chat-header">
        <img :src="otherUser?.avatar_url || defaultAvatar" alt="头像" class="chat-avatar" />
        <div class="chat-user-info">
          <span class="chat-name">{{ otherUser?.nickname || otherUser?.username || '未知用户' }}</span>
          <span class="chat-username">@{{ otherUser?.username }}</span>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="message-list" ref="messageListRef">
        <div class="messages-inner">
          <!-- 加载更多 -->
          <div class="load-more" v-if="hasMore">
            <button @click="loadMore">加载更早的消息</button>
          </div>

          <div
            v-for="msg in messages"
            :key="msg.id"
            class="message-item"
            :class="{ sent: msg.sender_id === MY_ID, received: msg.sender_id !== MY_ID }"
          >
            <div class="message-bubble">
              <span class="msg-content">{{ msg.content }}</span>
              <span class="msg-time">{{ formatMsgTime(msg.created_at) }}</span>
            </div>
          </div>

          <div class="no-more" v-if="!hasMore && messages.length > 0">
            <span>— 没有更多消息了 —</span>
          </div>
        </div>
      </div>

      <!-- 底部输入区 -->
      <div class="chat-input-area">
        <textarea
          v-model="newMessage"
          class="chat-input"
          placeholder="输入消息..."
          rows="2"
          @keydown.enter.exact.prevent="send"
        ></textarea>
        <button class="send-btn" @click="send" :disabled="!newMessage.trim()">
          <i class="fa-solid fa-paper-plane"></i>
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { getChatHistory, sendMessage, markAsRead, getUser } from '../api/index.js'

const route = useRoute()
const MY_ID = 1
const defaultAvatar = 'https://picsum.photos/seed/default/100/100'

const userId = computed(() => route.params.userId ? Number(route.params.userId) : null)
const otherUser = ref(null)
const messages = ref([])
const newMessage = ref('')
const messageListRef = ref(null)
const page = ref(1)
const pageSize = 50
const total = ref(0)
const hasMore = computed(() => messages.value.length < total.value)

function formatMsgTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function send() {
  const content = newMessage.value.trim()
  if (!content || !userId.value) return

  try {
    const msg = await sendMessage({
      sender_id: MY_ID,
      receiver_id: userId.value,
      content,
    })
    messages.value.push(msg)
    newMessage.value = ''
    total.value++
    await nextTick()
    scrollToBottom()
  } catch (e) {
    alert('发送失败: ' + e.message)
  }
}

async function loadMessages() {
  if (!userId.value) {
    messages.value = []
    otherUser.value = null
    return
  }

  page.value = 1
  try {
    const res = await getChatHistory(MY_ID, userId.value, {
      page: 1,
      page_size: pageSize,
    })
    messages.value = res.items.slice().reverse()
    total.value = res.total

    // 加载对方用户信息
    otherUser.value = await getUser(userId.value)

    // 标记为已读
    await markAsRead(MY_ID, userId.value)

    await nextTick()
    scrollToBottom()
  } catch (e) {
    console.error('加载聊天记录失败:', e)
  }
}

async function loadMore() {
  page.value++
  try {
    const res = await getChatHistory(MY_ID, userId.value, {
      page: page.value,
      page_size: pageSize,
    })
    messages.value = [...res.items.slice().reverse(), ...messages.value]
  } catch (e) {
    page.value--
    console.error('加载更多失败:', e)
  }
}

function scrollToBottom() {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

// 切换对话时重新加载
watch(() => route.params.userId, loadMessages)

onMounted(loadMessages)
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
}

/* 空状态 */
.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-gray);
  gap: 10px;
}

.chat-empty p {
  font-size: 15px;
  font-weight: 500;
}

.empty-sub {
  font-size: 12px;
}

/* 顶部header */
.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
  background: #fff;
  flex-shrink: 0;
}

.chat-avatar {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  object-fit: cover;
  background: #e0e0e0;
}

.chat-user-info {
  display: flex;
  flex-direction: column;
}

.chat-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-dark);
}

.chat-username {
  font-size: 11px;
  color: var(--text-gray);
}

/* 消息列表 */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: var(--chat-bg);
}

.messages-inner {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.load-more {
  text-align: center;
}

.load-more button {
  padding: 4px 16px;
  border: 1px solid var(--border-light);
  border-radius: 4px;
  background: #fff;
  color: var(--text-gray);
  cursor: pointer;
  font-size: 12px;
}

.no-more {
  text-align: center;
}

.no-more span {
  font-size: 11px;
  color: var(--text-gray);
}

/* 消息气泡 */
.message-item {
  display: flex;
  max-width: 75%;
}

.message-item.sent {
  align-self: flex-end;
}

.message-item.received {
  align-self: flex-start;
}

.message-bubble {
  padding: 8px 12px;
  border-radius: 12px;
  position: relative;
  word-break: break-word;
}

.message-item.sent .message-bubble {
  background: var(--primary-color);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-item.received .message-bubble {
  background: #fff;
  color: var(--text-dark);
  border: 1px solid var(--border-light);
  border-bottom-left-radius: 4px;
}

.msg-content {
  font-size: 13px;
  line-height: 1.5;
  display: block;
}

.msg-time {
  font-size: 10px;
  opacity: 0.6;
  display: block;
  margin-top: 2px;
  text-align: right;
}

/* 输入区 */
.chat-input-area {
  display: flex;
  gap: 8px;
  padding: 10px 16px;
  border-top: 1px solid var(--border-light);
  background: #fff;
  align-items: flex-end;
  flex-shrink: 0;
}

.chat-input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid var(--border-light);
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  resize: none;
  font-family: inherit;
  max-height: 80px;
}

.chat-input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(18, 183, 245, 0.15);
}

.send-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: var(--primary-color);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  flex-shrink: 0;
  font-size: 14px;
}

.send-btn:hover {
  background: var(--primary-hover);
}

.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
