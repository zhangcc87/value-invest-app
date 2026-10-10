<template>
  <el-container style="height: 100vh;">
    <el-aside :width="collapse ? '64px' : '200px'" style="background-color: var(--el-bg-color);border-right:1px solid var(--el-border-color);transition: width 0.3s;">
      <div class="sidebar-container">
        <!-- 顶部系统名称+图标 -->
        <div class="sidebar-header">
          <el-icon size="24"><Box /></el-icon>
          <span v-if="!collapse" class="sys-name">FastAPI管理后台</span>
        </div>

        <el-menu
          router
          :collapse="collapse"
          collapse-transition
          default-active="$route.path"
          background-color="var(--el-bg-color)"
          text-color="var(--el-text-color-primary)"
          active-text-color="#409eff"
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>
          <el-menu-item index="/users">
            <el-icon><User /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
        </el-menu>

        <!-- 底部主题下拉 -->
        <div class="sidebar-footer">
          <el-select v-model="themeMode" @change="handleThemeChange" :disabled="collapse" style="width:100%">
            <el-option label="浅色模式" value="light"></el-option>
            <el-option label="暗黑模式" value="dark"></el-option>
          </el-select>
        </div>
      </div>
    </el-aside>

    <el-container>
      <el-header style="background:var(--el-bg-color);display:flex;justify-content:space-between;align-items:center;padding:0 20px;border-bottom:1px solid var(--el-border-color);">
        <div class="header-left">
          <!-- 收缩展开按钮 -->
          <el-button text @click="collapse = !collapse">
            <el-icon size="20">
              <Expand v-if="collapse"/>
              <Fold v-else/>
            </el-icon>
          </el-button>
        </div>

        <div style="display:flex;align-items:center;gap:16px;">
          <span v-if="currentUser">{{ currentUser.email }}</span>
          <el-button type="text" @click="logout">退出登录</el-button>
        </div>
      </el-header>

      <el-main style="background-color:var(--el-bg-color);">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Box, House, User, Fold, Expand } from '@element-plus/icons-vue'
import request from '@/api/request'

const router = useRouter()

interface CurrentUser {
  id: number
  email: string
  is_superuser: boolean
}
const currentUser = ref<CurrentUser | null>(null)

// 侧边栏收缩
const collapse = ref(false)
const themeMode = ref<'light' | 'dark'>('light')

// 监听主题变化，html增加/移除 class="dark"（官方标准）
watch(themeMode, (val) => {
  if(val === 'dark'){
    document.documentElement.classList.add('dark')
  }else{
    document.documentElement.classList.remove('dark')
  }
  localStorage.setItem('app-theme', val)
},{immediate:true})

const handleThemeChange = (val: string) => {
  themeMode.value = val as 'light' | 'dark'
}

// 获取当前登录用户信息
const fetchMe = async () => {
  try {
    const res = await request.get('/users/me')
    currentUser.value = res
  } catch (err) {
    console.error("获取用户信息失败", err)
  }
}

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}

// 页面加载读取上次保存的主题
onMounted(() => {
  fetchMe()
  const savedTheme = localStorage.getItem('app-theme')
  if(savedTheme){
    themeMode.value = savedTheme as 'light' | 'dark'
  }
})
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 56px;
  padding: 0 16px;
  border-bottom: 1px solid var(--el-border-color);
}
.sys-name {
  font-size:16px;
  font-weight: 600;
}
.sidebar-container :deep(.el-menu) {
  border-right: none;
  flex:1;
}
.sidebar-footer {
  padding:12px 8px;
  border-top: 1px solid var(--el-border-color);
}
.header-left {
  display:flex;
  align-items:center;
}

/* ========== 自定义浅色模式菜单hover样式 ========== */
:root:not(.dark) .el-menu-item:hover {
  --el-menu-hover-bg-color: #f5f7fa !important;
}
/* 激活选中的菜单背景，同步调浅 */
:root:not(.dark) .el-menu-item.is-active {
  --el-menu-active-bg-color: #ecf5ff !important;
}
</style>
