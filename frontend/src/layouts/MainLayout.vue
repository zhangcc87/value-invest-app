<template>
    <el-container style="height: 100vh">
        <el-aside
            :width="collapse ? '64px' : '240px'"
            style="
                background-color: var(--el-bg-color);
                border-right: 1px solid var(--el-border-color);
                transition: width 0.3s;
            "
        >
            <div class="sidebar-container">
                <!-- 顶部系统名称+图标 -->
                <div class="sidebar-header">
                    <el-icon size="20"><Box /></el-icon>
                    <span v-if="!collapse" class="sys-name"
                        >Value Invest App</span
                    >
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
                    <el-select
                        v-model="themeMode"
                        @change="handleThemeChange"
                        :disabled="collapse"
                        style="width: 100%"
                    >
                        <el-option label="浅色模式" value="light"></el-option>
                        <el-option label="暗黑模式" value="dark"></el-option>
                    </el-select>
                </div>
            </div>
        </el-aside>

        <el-container>
            <el-header
                style="
                    background: var(--el-bg-color);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0 20px;
                    border-bottom: 1px solid var(--el-border-color);
                "
            >
                <div class="header-left">
                    <!-- 收缩展开按钮 -->
                    <el-button text @click="collapse = !collapse">
                        <el-icon size="20">
                            <Expand v-if="collapse" />
                            <Fold v-else />
                        </el-icon>
                    </el-button>
                </div>

                <div class="header-right">
                    <!-- 用户下拉菜单 -->
                    <el-dropdown @command="handleUserCommand">
                        <span class="user-dropdown-text">
                            {{ currentUser?.email }}
                            <el-icon><ArrowDown /></el-icon>
                        </span>
                        <template #dropdown>
                            <el-dropdown-menu>
                                <el-dropdown-item command="settings">
                                    <el-icon><Setting /></el-icon>
                                    用户设置
                                </el-dropdown-item>
                                <el-dropdown-item command="logout" divided>
                                    <el-icon><TurnOff /></el-icon>
                                    退出登录
                                </el-dropdown-item>
                            </el-dropdown-menu>
                        </template>
                    </el-dropdown>
                </div>
            </el-header>

            <el-main style="background-color: var(--el-bg-color)">
                <router-view />
            </el-main>
        </el-container>
    </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import {
    Box,
    House,
    User,
    Fold,
    Expand,
    ArrowDown,
    Setting,
    TurnOff,
} from "@element-plus/icons-vue";
import request from "@/api/request";

const router = useRouter();

interface CurrentUser {
    id: number;
    email: string;
    is_superuser: boolean;
}
const currentUser = ref<CurrentUser | null>(null);

// 侧边栏收缩
const collapse = ref(false);
const themeMode = ref<"light" | "dark">("light");

const handleUserCommand = (cmd: string) => {
    if (cmd === "settings") {
        router.push("/settings");
    } else if (cmd === "logout") {
        localStorage.removeItem("token");
        router.push("/login");
    }
};

// 监听主题变化，html增加/移除 class="dark"（官方标准）
watch(
    themeMode,
    (val) => {
        if (val === "dark") {
            document.documentElement.classList.add("dark");
        } else {
            document.documentElement.classList.remove("dark");
        }
        localStorage.setItem("app-theme", val);
    },
    { immediate: true }
);

const handleThemeChange = (val: string) => {
    themeMode.value = val as "light" | "dark";
};

// 获取当前登录用户信息
const fetchMe = async () => {
    try {
        const res = await request.get("/users/me");
        currentUser.value = res;
    } catch (err) {
        console.error("获取用户信息失败", err);
    }
};

const logout = () => {
    localStorage.removeItem("token");
    router.push("/login");
};

// 页面加载读取上次保存的主题
onMounted(() => {
    fetchMe();
    const savedTheme = localStorage.getItem("app-theme");
    if (savedTheme) {
        themeMode.value = savedTheme as "light" | "dark";
    }
});
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
    /* ========== 移除标题下方分割线 ========== */
    border-bottom: none;
    padding: 0 20px; /* ✅ 和 el-menu-item 的左右内边距保持一致，实现水平对齐 */
}
.sidebar-header .el-icon {
    font-size: 20px; /* ✅ 和菜单图标大小统一 */
}
.sys-name {
    font-size: 16px;
    font-weight: 600;
    white-space: nowrap; /* 禁止文字换行 */
    overflow: hidden; /* 超出部分隐藏 */
    text-overflow: ellipsis; /* 文字过长显示省略号 */
}
.sidebar-container :deep(.el-menu) {
    border-right: none;
    flex: 1;
}
.sidebar-footer {
    padding: 12px 8px;
    border-top: none;
}
.header-left {
    display: flex;
    align-items: center;
}

/* ========== 浅色模式菜单hover 保持浅背景 ========== */
:root:not(.dark) .el-menu-item:hover {
    --el-menu-hover-bg-color: #f5f7fa !important;
}
:root:not(.dark) .el-menu-item.is-active {
    --el-menu-active-bg-color: #ecf5ff !important;
}

/* ========== 移除所有 el-card 标题下分割线 ========== */
:deep(.el-card__header) {
    border-bottom: none !important;
}

.header-right {
    display: flex;
    align-items: center;
}
.user-dropdown-text {
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;
    color: var(--el-text-color-primary);
}
</style>
