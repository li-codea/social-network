<template>
  <div class="recommend-view">
    <div class="rec-header">
      <h3>好友推荐</h3>
      <select v-model.number="maxDegree">
        <option :value="2">二度好友</option>
        <option :value="3">二度&三度好友</option>
      </select>
    </div>
    <div class="rec-list" v-if="recommendations.length > 0">
      <div
        v-for="rec in recommendations"
        :key="rec.user.id"
        class="rec-item"
        @click="selectUser(rec.user)"
      >
        <img :src="rec.user.avatar_url || defaultAvatar" alt="头像" class="rec-avatar" />
        <div class="rec-info">
          <div class="rec-name">{{ rec.user.nickname || rec.user.username }}</div>
          <div class="rec-reason">
            <span v-if="rec.reason.common_friends_count" class="reason-tag">
              <i class="fa-solid fa-user-group"></i>
              {{ rec.reason.common_friends_count }}个共同好友
            </span>
            <span v-if="rec.reason.common_tags_count" class="reason-tag">
              <i class="fa-solid fa-tag"></i>
              {{ rec.reason.common_tags_count }}个共同标签
            </span>
            <span v-if="rec.reason.degree" class="reason-tag">
              <i class="fa-solid fa-circle-nodes"></i>
              {{ rec.reason.degree }}度人脉
            </span>
          </div>
          <div class="rec-tags" v-if="rec.reason.common_tags?.length">
            <span class="tag" v-for="tag in rec.reason.common_tags.slice(0, 5)" :key="tag">
              {{ tag }}
            </span>
          </div>
        </div>
        <div class="rec-score">{{ rec.score }}分</div>
        <button class="add-btn" @click.stop="quickAddFriend(rec.user)">
          <i class="fa-solid fa-user-plus"></i>
        </button>
      </div>
    </div>
    <div class="empty-list" v-else>
      <i class="fa-solid fa-star fa-2x"></i>
      <p>暂无推荐</p>
      <p class="sub-text">添加更多好友来获得推荐</p>
    </div>
    <div class="pagination" v-if="total > pageSize">
      <button :disabled="page <= 1" @click="changePage(-1)">上一页</button>
      <span>{{ page }} / {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="changePage(1)">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getRecommendations, addFriendship, getFriends } from '../api/index.js'

const router = useRouter()
const MY_ID = 1

const recommendations = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const maxDegree = ref(3)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const defaultAvatar = 'https://picsum.photos/seed/default/100/100'

async function loadRecommendations() {
  try {
    const res = await getRecommendations(MY_ID, {
      page: page.value,
      page_size: pageSize.value,
      max_degree: maxDegree.value,
    })
    recommendations.value = res.items
    total.value = res.total
  } catch (e) {
    console.error('加载推荐失败:', e)
  }
}

function changePage(delta) {
  page.value += delta
  loadRecommendations()
}

function selectUser(user) {
  router.push({ name: 'Profile', params: { id: user.id } })
}

async function quickAddFriend(user) {
  try {
    await addFriendship({ user_id: MY_ID, friend_id: user.id })
    // 从推荐列表中移除
    recommendations.value = recommendations.value.filter(r => r.user.id !== user.id)
    total.value--
    alert(`已添加 ${user.nickname || user.username} 为好友`)
  } catch (e) {
    alert('添加失败: ' + e.message)
  }
}

watch(maxDegree, () => {
  page.value = 1
  loadRecommendations()
})

onMounted(loadRecommendations)
</script>

<style scoped>
.recommend-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.rec-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-light);
}

.rec-header h3 {
  font-size: 15px;
  color: var(--text-dark);
}

.rec-header select {
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid var(--border-light);
  font-size: 12px;
  outline: none;
}

.rec-list {
  flex: 1;
  overflow-y: auto;
}

.rec-item {
  display: flex;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
  align-items: flex-start;
  border-bottom: 1px solid rgba(0,0,0,0.04);
}

.rec-item:hover {
  background: rgba(255, 255, 255, 0.6);
}

.rec-avatar {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  margin-right: 10px;
  object-fit: cover;
  background: #e0e0e0;
}

.rec-info {
  flex: 1;
  overflow: hidden;
  margin-right: 8px;
}

.rec-name {
  font-size: 14px;
  color: var(--text-dark);
  font-weight: 500;
  margin-bottom: 4px;
}

.rec-reason {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.reason-tag {
  font-size: 10px;
  color: var(--text-gray);
  display: flex;
  align-items: center;
  gap: 3px;
}

.rec-tags {
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

.rec-score {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary-color);
  margin-right: 8px;
  white-space: nowrap;
  align-self: center;
}

.add-btn {
  background: none;
  border: none;
  color: var(--primary-color);
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
  align-self: center;
  transition: transform 0.2s;
}

.add-btn:hover {
  transform: scale(1.2);
}

.empty-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-gray);
  gap: 4px;
}

.empty-list p {
  font-size: 13px;
}

.sub-text {
  font-size: 11px !important;
  color: #bbb;
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
