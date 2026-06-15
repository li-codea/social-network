<template>
  <div class="sidebar-nav">
    <div class="avatar-wrapper">
      <img
        :src="myAvatar"
        alt="我的头像"
        class="my-avatar"
        @click="$emit('navigate', 'Profile')"
      />
      <div class="status-dot"></div>
    </div>
    <div class="nav-icons">
      <div
        v-for="item in navItems"
        :key="item.route"
        class="nav-icon"
        :class="{ active: currentRoute === item.route }"
        :title="item.label"
        @click="$emit('navigate', item.route)"
      >
        <i :class="item.icon"></i>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  currentRoute: String,
})
defineEmits(['navigate'])

const myAvatar = 'https://picsum.photos/seed/myavatar/100/100'

const navItems = [
  { route: 'Messages', icon: 'fa-solid fa-comment fa-lg', label: '消息' },
  { route: 'Friends', icon: 'fa-solid fa-address-book fa-lg', label: '好友' },
  { route: 'Search', icon: 'fa-solid fa-magnifying-glass fa-lg', label: '发现用户' },
  { route: 'Recommend', icon: 'fa-solid fa-star fa-lg', label: '好友推荐' },
  { route: 'Profile', icon: 'fa-solid fa-user fa-lg', label: '个人资料' },
]
</script>

<style scoped>
.sidebar-nav {
  width: 64px;
  min-width: 64px;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  user-select: none;
}

.avatar-wrapper {
  position: relative;
  margin-bottom: 30px;
}

.my-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid transparent;
  transition: border-color 0.3s;
  cursor: pointer;
}

.my-avatar:hover {
  border-color: var(--primary-color);
}

.status-dot {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 10px;
  height: 10px;
  background: var(--success-color);
  border-radius: 50%;
  border: 2px solid var(--sidebar-bg);
}

.nav-icons {
  display: flex;
  flex-direction: column;
  gap: 24px;
  align-items: center;
}

.nav-icon {
  color: #989898;
  cursor: pointer;
  transition: color 0.2s, transform 0.2s;
  position: relative;
}

.nav-icon:hover,
.nav-icon.active {
  color: var(--primary-color);
  transform: scale(1.1);
}
</style>
