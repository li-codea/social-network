/**
 * API 客户端模块
 * 封装所有后端 API 调用，统一错误处理
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// 响应拦截器：统一提取 data
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const detail = error.response?.data?.detail || '网络请求失败'
    return Promise.reject(new Error(detail))
  }
)

// ==================== 用户 API ====================

/** 创建用户 */
export function createUser(data) {
  return api.post('/users/', data)
}

/** 获取用户列表（分页+搜索） */
export function getUsers(params = {}) {
  return api.get('/users/', { params })
}

/** 获取单个用户 */
export function getUser(userId) {
  return api.get(`/users/${userId}`)
}

/** 更新用户 */
export function updateUser(userId, data) {
  return api.put(`/users/${userId}`, data)
}

/** 删除用户 */
export function deleteUser(userId) {
  return api.delete(`/users/${userId}`)
}

// ==================== 好友 API ====================

/** 获取用户好友列表 */
export function getFriends(userId, params = {}) {
  return api.get(`/users/${userId}/friends`, { params })
}

/** 获取共同好友 */
export function getCommonFriends(userId, otherId) {
  return api.get(`/users/${userId}/common-friends/${otherId}`)
}

/** 获取好友推荐 */
export function getRecommendations(userId, params = {}) {
  return api.get(`/users/${userId}/recommendations`, { params })
}

/** 添加好友 */
export function addFriendship(data) {
  return api.post('/friendships/', data)
}

/** 解除好友（按关系ID） */
export function removeFriendship(friendshipId) {
  return api.delete(`/friendships/${friendshipId}`)
}

/** 解除好友（按用户ID） */
export function removeFriendshipByUsers(userId, friendId) {
  return api.delete('/friendships/users', { params: { user_id: userId, friend_id: friendId } })
}

/** 检查好友关系 */
export function checkFriendship(userId, otherId) {
  return api.get('/friendships/exists', { params: { user_id: userId, other_id: otherId } })
}

// ==================== 聊天 API ====================

/** 发送消息 */
export function sendMessage(data) {
  return api.post('/messages/', data)
}

/** 获取会话列表 */
export function getConversations(userId, params = {}) {
  return api.get('/messages/conversations', { params: { user_id: userId, ...params } })
}

/** 获取聊天记录 */
export function getChatHistory(userId, otherId, params = {}) {
  return api.get('/messages/', { params: { user_id: userId, other_id: otherId, ...params } })
}

/** 标记已读 */
export function markAsRead(userId, otherId) {
  return api.put('/messages/read', null, { params: { user_id: userId, other_id: otherId } })
}
