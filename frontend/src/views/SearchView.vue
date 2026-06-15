<template>
  <div class="search-view">
    <div class="search-bar">
      <i class="fa-solid fa-magnifying-glass"></i>
      <input
        v-model="keyword"
        type="text"
        placeholder="按昵称或用户名搜索..."
        @input="onSearch"
        autofocus
      />
    </div>
    <div class="user-list" v-if="users.length > 0">
      <div
        v-for="user in users"
        :key="user.id"
        class="user-item"
        @click="selectUser(user)"
      >
        <img :src="user.avatar_url || defaultAvatar" alt="头像" class="user-avatar" />
        <div class="user-info">
          <div class="user-name">{{ user.nickname || user.username }}</div>
          <div class="user-username">@{{ user.username }}</div>
          <div class="user-tags" v-if="user.tags?.length">
            <span class="tag" v-for="tag in user.tags" :key="tag">{{ tag }}</span>
          </div>
        </div>
        <button class="add-friend-btn" v-if="user.id !== MY_ID && !friendIds.has(user.id)" @click.stop="addFriend(user)">
          <i class="fa-solid fa-user-plus"></i> 加好友
        </button>
        <span class="already-friend" v-else-if="user.id !== MY_ID">
          <i class="fa-solid fa-check"></i> 已添加
        </span>
        <button class="chat-btn" v-if="user.id !== MY_ID" @click.stop="startChat(user.id)">
          <i class="fa-solid fa-comment"></i>
        </button>
      </div>
    </div>
    <div class="empty-list" v-else-if="searched">
      <i class="fa-solid fa-magnifying-glass fa-2x"></i>
      <p>没有找到匹配的用户</p>
    </div>
    <div class="empty-list" v-else>
      <i class="fa-solid fa-search fa-2x"></i>
      <p>输入关键词搜索用户</p>
    </div>
    <div class="pagination" v-if="total > pageSize">
      <button :disabled="page <= 1" @click="changePage(-1)">上一页</button>
      <span>{{ page }} / {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="changePage(1)">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getUsers, addFriendship } from '../api/index.js'

const router = useRouter()
const MY_ID = 1

const users = ref([])
const keyword = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searched = ref(false)
const friendIds = ref(new Set())
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const defaultAvatar = 'https://picsum.photos/seed/default/100/100'

let searchTimer = null

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    searched.value = true
    loadUsers()
  }, 400)
}

function changePage(delta) {
  page.value += delta
  loadUsers()
}

async function loadUsers() {
  try {
    const res = await getUsers({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
    })
    users.value = res.items
    total.value = res.total
  } catch (e) {
    console.error('搜索失败:', e)
  }
}

async function loadFriendIds() {
  try {
    const { getFriends } = await import('../api/index.js')
    const res = await getFriends(MY_ID, { page: 1, page_size: 1000 })
    friendIds.value = new Set(res.items.map(f => f.id))
  } catch (e) {
    console.error('加载好友列表失败:', e)
  }
}

async function addFriend(user) {
  try {
    await addFriendship({ user_id: MY_ID, friend_id: user.id })
    friendIds.value.add(user.id)
    alert(`已添加 ${user.nickname || user.username} 为好友`)
  } catch (e) {
    alert('添加失败: ' + e.message)
  }
}

function selectUser(user) {
  router.push({ name: 'Profile', params: { id: user.id } })
}

function startChat(userId) {
  router.push({ name: 'Messages', params: { userId } })
}

onMounted(() => {
  loadFriendIds()
  loadUsers()
})
</script>

<style scoped>
.search-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.search-bar {
  padding: 16px;
  position: relative;
}

.search-bar input {
  width: 100%;
  height: 36px;
  border-radius: 8px;
  border: none;
  background: rgba(255, 255, 255, 0.8);
  padding: 0 12px 0 36px;
  font-size: 13px;
  outline: none;
}

.search-bar input:focus {
  box-shadow: 0 0 0 2px rgba(18, 183, 245, 0.3);
  background: #fff;
}

.search-bar i {
  position: absolute;
  left: 28px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-gray);
  font-size: 13px;
}

.user-list {
  flex: 1;
  overflow-y: auto;
}

.user-item {
  display: flex;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
  align-items: center;
  border-bottom: 1px solid rgba(0,0,0,0.04);
}

.user-item:hover {
  background: rgba(255, 255, 255, 0.6);
}

.user-avatar {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  margin-right: 12px;
  object-fit: cover;
  background: #e0e0e0;
}

.user-info {
  flex: 1;
  overflow: hidden;
}

.user-name {
  font-size: 14px;
  color: var(--text-dark);
  font-weight: 500;
}

.user-username {
  font-size: 11px;
  color: var(--text-gray);
  margin-bottom: 2px;
}

.user-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 3px;
}

.tag {
  font-size: 10px;
  color: var(--primary-color);
  background: rgba(18, 183, 245, 0.1);
  padding: 1px 6px;
  border-radius: 4px;
}

.add-friend-btn {
  padding: 4px 10px;
  border: 1px solid var(--primary-color);
  border-radius: 4px;
  background: #fff;
  color: var(--primary-color);
  cursor: pointer;
  font-size: 11px;
  white-space: nowrap;
  transition: all 0.2s;
}

.add-friend-btn:hover {
  background: var(--primary-color);
  color: #fff;
}

.already-friend {
  font-size: 11px;
  color: var(--success-color);
  white-space: nowrap;
}

.chat-btn {
  padding: 4px 10px;
  border: 1px solid var(--success-color);
  border-radius: 4px;
  background: #fff;
  color: var(--success-color);
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
  transition: all 0.2s;
  margin-left: 4px;
}

.chat-btn:hover {
  background: var(--success-color);
  color: #fff;
}

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
  font-size: 13px;
}

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
