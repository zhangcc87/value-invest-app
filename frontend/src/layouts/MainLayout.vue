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
        <span>Full Stack FastAPI + Vue3</span>
        <el-button type="text" @click="logout">退出登录</el-button>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { House, User } from '@element-plus/icons-vue'
const router = useRouter()

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>