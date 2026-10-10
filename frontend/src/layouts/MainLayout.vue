<template>
  <el-container style="height: 100vh;">
    <el-aside width="200px" style="background-color: #001529;">
      <el-menu
        router
        default-active="$route.path"
        background-color="#001529"
        text-color="#fff"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><House /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="background:#fff;display:flex;justify-content:space-between;align-items:center;padding:0 20px;border-bottom:1px solid #eee;">
        <span>股票管理系统</span>
        <div style="display:flex;align-items:center;gap:16px;">
          <span v-if="currentUser">{{ currentUser.email }}</span>
          <el-button type="text" @click="logout">退出登录</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { House, User } from '@element-plus/icons-vue'
import request from '@/api/request'

const router = useRouter()

interface CurrentUser {
  id: string
  email: string
  is_superuser: boolean
}
const currentUser = ref<CurrentUser | null>(null)

// 获取当前登录用户信息
const fetchMe = async () => {
  try {
    const res = await request.get('/users/me')
    currentUser.value = res
  } catch (err) {
    // 401会在request拦截器处理，自动跳转登录
    console.error("获取用户信息失败", err)
  }
}

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}

onMounted(() => {
  fetchMe()
})
</script>