<template>
  <div class="friends-view">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <i class="fa-solid fa-magnifying-glass"></i>
      <input
        v-model="searchKeyword"
        type="text"
        placeholder="搜索好友..."
        @input="onSearch"
      />
    </div>
    <!-- 好友列表 -->
    <div class="friend-list" v-if="friends.length > 0">
      <div
        v-for="user in friends"
        :key="user.id"
        class="friend-item"
        :class="{ selected: selectedId === user.id }"
        @click="selectFriend(user)"
      >
        <img :src="user.avatar_url || defaultAvatar" alt="头像" class="friend-avatar" />
        <div class="friend-info">
          <div class="friend-name">{{ user.nickname || user.username }}</div>
          <div class="friend-tags" v-if="user.tags?.length">
            <span class="tag" v-for="tag in user.tags.slice(0, 3)" :key="tag">{{ tag }}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="empty-list" v-else>
      <i class="fa-solid fa-user-slash fa-2x"></i>
      <p>{{ searchKeyword ? '没有找到匹配的好友' : '还没有好友' }}</p>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getFriends, getUser } from '../api/index.js'

const router = useRouter()
const MY_ID = 1 // 当前登录用户ID（模拟）

const friends = ref([])
const selectedId = ref(null)
const searchKeyword = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const defaultAvatar = 'https://picsum.photos/seed/default/100/100'

let searchTimer = null

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadFriends()
  }, 300)
}

function changePage(delta) {
  page.value += delta
  loadFriends()
}

async function loadFriends() {
  try {
    const res = await getFriends(MY_ID, {
      page: page.value,
      page_size: pageSize.value,
    })
    // API returns paginated response, filter by search keyword on client side
    friends.value = res.items.filter(f => {
      if (!searchKeyword.value) return true
      const kw = searchKeyword.value.toLowerCase()
      return (f.nickname || f.username).toLowerCase().includes(kw)
    })
    total.value = res.total
  } catch (e) {
    console.error('加载好友失败:', e)
  }
}

function selectFriend(user) {
  selectedId.value = user.id
  router.push({ name: 'Profile', params: { id: user.id } })
}

onMounted(loadFriends)
</script>

<style scoped>
.friends-view {
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
  transition: box-shadow 0.3s;
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

.friend-list {
  flex: 1;
  overflow-y: auto;
}

.friend-item {
  display: flex;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
  align-items: center;
}

.friend-item:hover {
  background: rgba(255, 255, 255, 0.5);
}

.friend-item.selected {
  background: rgba(18, 183, 245, 0.15);
}

.friend-avatar {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  margin-right: 12px;
  object-fit: cover;
  background: #e0e0e0;
}

.friend-info {
  flex: 1;
  overflow: hidden;
}

.friend-name {
  font-size: 14px;
  color: var(--text-dark);
  font-weight: 500;
  margin-bottom: 4px;
}

.friend-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.tag {
  font-size: 10px;
  color: var(--primary-color);
  background: rgba(18, 183, 245, 0.1);
  padding: 1px 6px;
  border-radius: 4px;
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
