<template>
  <div class="profile-view" v-if="user">
    <!-- 用户信息头部 -->
    <div class="profile-header">
      <img :src="user.avatar_url || defaultAvatar" alt="头像" class="profile-avatar" />
      <div class="profile-basic">
        <h2>{{ user.nickname || user.username }}</h2>
        <p class="username">@{{ user.username }}</p>
        <p class="bio" v-if="user.bio">{{ user.bio }}</p>
      </div>
      <div class="profile-actions" v-if="user.id !== MY_ID">
        <button v-if="!isFriend" class="btn-primary" @click="handleAddFriend">
          <i class="fa-solid fa-user-plus"></i> 加好友
        </button>
        <button v-else class="btn-danger" @click="handleRemoveFriend">
          <i class="fa-solid fa-user-minus"></i> 解除好友
        </button>
        <button class="btn-chat" @click="handleStartChat(user.id)">
          <i class="fa-solid fa-comment"></i> 发消息
        </button>
      </div>
      <div class="profile-actions" v-else>
        <button class="btn-edit" @click="toggleEdit">
          <i class="fa-solid fa-pen"></i> 编辑资料
        </button>
      </div>
    </div>

    <!-- 标签 -->
    <div class="section" v-if="user.tags?.length">
      <h4>兴趣标签</h4>
      <div class="tags-wrap">
        <span class="tag" v-for="tag in user.tags" :key="tag">{{ tag }}</span>
      </div>
    </div>

    <!-- 编辑表单（仅自己） -->
    <div class="section edit-form" v-if="isEditing">
      <h4>编辑资料</h4>
      <div class="form-group">
        <label>昵称</label>
        <input v-model="editForm.nickname" type="text" placeholder="输入昵称" />
      </div>
      <div class="form-group">
        <label>头像URL</label>
        <input v-model="editForm.avatar_url" type="text" placeholder="输入头像图片URL" />
      </div>
      <div class="form-group">
        <label>个人简介</label>
        <textarea v-model="editForm.bio" rows="3" placeholder="写一段自我介绍..."></textarea>
      </div>
      <div class="form-group">
        <label>兴趣标签（逗号分隔）</label>
        <input
          v-model="editForm.tagsInput"
          type="text"
          placeholder="如: Python, 篮球, 摄影"
        />
      </div>
      <div class="form-actions">
        <button class="btn-primary" @click="handleSave">保存</button>
        <button class="btn-cancel" @click="toggleEdit">取消</button>
      </div>
    </div>

    <!-- 好友列表（仅自己可见完整） -->
    <div class="section" v-if="friendList.length > 0">
      <h4>好友 ({{ friendTotal }})</h4>
      <div class="mini-friends">
        <div
          v-for="f in friendList"
          :key="f.id"
          class="mini-friend"
          @click="router.push({ name: 'Profile', params: { id: f.id } })"
        >
          <img :src="f.avatar_url || defaultAvatar" alt="头像" />
          <span>{{ f.nickname || f.username }}</span>
        </div>
      </div>
    </div>

    <!-- 共同好友（仅他人可见） -->
    <div class="section" v-if="user.id !== MY_ID && commonFriends.length > 0">
      <h4>共同好友 ({{ commonFriends.length }})</h4>
      <div class="mini-friends">
        <div
          v-for="f in commonFriends"
          :key="f.id"
          class="mini-friend"
          @click="router.push({ name: 'Profile', params: { id: f.id } })"
        >
          <img :src="f.avatar_url || defaultAvatar" alt="头像" />
          <span>{{ f.nickname || f.username }}</span>
        </div>
      </div>
    </div>

    <!-- 注册时间 -->
    <div class="section meta">
      <p>注册时间: {{ formatDate(user.created_at) }}</p>
      <p>最后更新: {{ formatDate(user.updated_at) }}</p>
    </div>
  </div>

  <div class="profile-view" v-else>
    <div class="loading">加载中...</div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getUser, updateUser, getFriends, getCommonFriends,
  addFriendship, checkFriendship, removeFriendshipByUsers,
} from '../api/index.js'

const route = useRoute()
const router = useRouter()
const MY_ID = 1

const user = ref(null)
const isFriend = ref(false)
const friendList = ref([])
const friendTotal = ref(0)
const commonFriends = ref([])
const isEditing = ref(false)
const editForm = ref({
  nickname: '',
  avatar_url: '',
  bio: '',
  tagsInput: '',
})

const defaultAvatar = 'https://picsum.photos/seed/default/100/100'

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function toggleEdit() {
  if (isEditing.value) {
    isEditing.value = false
  } else {
    editForm.value = {
      nickname: user.value?.nickname || '',
      avatar_url: user.value?.avatar_url || '',
      bio: user.value?.bio || '',
      tagsInput: (user.value?.tags || []).join(', '),
    }
    isEditing.value = true
  }
}

async function handleSave() {
  try {
    const data = {}
    if (editForm.value.nickname) data.nickname = editForm.value.nickname
    if (editForm.value.avatar_url) data.avatar_url = editForm.value.avatar_url
    if (editForm.value.bio) data.bio = editForm.value.bio
    if (editForm.value.tagsInput) {
      data.tags = editForm.value.tagsInput.split(',').map(t => t.trim()).filter(Boolean)
    }
    await updateUser(user.value.id, data)
    isEditing.value = false
    await loadUser()
  } catch (e) {
    alert('保存失败: ' + e.message)
  }
}

async function handleAddFriend() {
  try {
    await addFriendship({ user_id: MY_ID, friend_id: user.value.id })
    isFriend.value = true
    alert('已添加好友')
  } catch (e) {
    alert('添加失败: ' + e.message)
  }
}

async function handleRemoveFriend() {
  if (!confirm('确定解除好友关系？')) return
  try {
    await removeFriendshipByUsers(MY_ID, user.value.id)
    isFriend.value = false
    alert('已解除好友关系')
  } catch (e) {
    alert('解除失败: ' + e.message)
  }
}

function handleStartChat(userId) {
  router.push({ name: 'Messages', params: { userId } })
}

async function loadUser() {
  const userId = route.params.id || MY_ID
  try {
    user.value = await getUser(userId)
    // 加载好友列表
    const friendsRes = await getFriends(userId, { page: 1, page_size: 100 })
    friendList.value = friendsRes.items
    friendTotal.value = friendsRes.total

    // 若不是自己，检查好友关系和共同好友
    if (Number(userId) !== MY_ID) {
      try {
        const checkRes = await checkFriendship(MY_ID, userId)
        isFriend.value = checkRes.are_friends
      } catch (e) { /* ignore */ }

      try {
        const commonRes = await getCommonFriends(MY_ID, userId)
        commonFriends.value = commonRes.common_friends || []
      } catch (e) { /* ignore */ }
    }
  } catch (e) {
    console.error('加载用户失败:', e)
  }
}

watch(() => route.params.id, loadUser)
onMounted(loadUser)
</script>

<style scoped>
.profile-view {
  padding: 24px;
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-gray);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.profile-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  object-fit: cover;
  background: #e0e0e0;
  border: 3px solid var(--primary-color);
}

.profile-basic {
  flex: 1;
}

.profile-basic h2 {
  font-size: 20px;
  color: var(--text-dark);
  margin-bottom: 2px;
}

.username {
  font-size: 13px;
  color: var(--text-gray);
  margin-bottom: 4px;
}

.bio {
  font-size: 13px;
  color: var(--text-dark);
  line-height: 1.4;
}

.profile-actions {
  display: flex;
  gap: 8px;
}

.btn-primary {
  padding: 6px 16px;
  background: var(--primary-color);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: var(--primary-hover);
}

.btn-danger {
  padding: 6px 16px;
  background: #fff;
  color: var(--danger-color);
  border: 1px solid var(--danger-color);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.btn-edit {
  padding: 6px 16px;
  background: #fff;
  color: var(--primary-color);
  border: 1px solid var(--primary-color);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.btn-chat {
  padding: 6px 16px;
  background: var(--success-color);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: opacity 0.2s;
}

.btn-chat:hover {
  opacity: 0.85;
}

.btn-cancel {
  padding: 6px 16px;
  background: #fff;
  color: var(--text-gray);
  border: 1px solid var(--border-light);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

/* 标签 */
.section {
  margin-bottom: 20px;
}

.section h4 {
  font-size: 13px;
  color: var(--text-gray);
  margin-bottom: 8px;
  font-weight: 500;
}

.tags-wrap {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  font-size: 12px;
  color: var(--primary-color);
  background: rgba(18, 183, 245, 0.08);
  padding: 4px 10px;
  border-radius: 12px;
}

/* 迷你好友列表 */
.mini-friends {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.mini-friend {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  gap: 4px;
}

.mini-friend img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  background: #e0e0e0;
}

.mini-friend span {
  font-size: 11px;
  color: var(--text-dark);
  max-width: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 编辑表单 */
.edit-form {
  background: var(--panel-bg);
  padding: 16px;
  border-radius: 8px;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 12px;
  color: var(--text-gray);
  margin-bottom: 4px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--border-light);
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  font-family: inherit;
  resize: vertical;
}

.form-group input:focus,
.form-group textarea:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(18, 183, 245, 0.15);
}

.form-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.meta {
  color: var(--text-gray);
  font-size: 12px;
  line-height: 1.8;
}
</style>
