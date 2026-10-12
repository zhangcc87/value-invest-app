<template>
    <div class="login-page">
        <el-card class="login-card">
            <h2 class="title">系统登录</h2>
            <el-form :model="form" label-width="80px">
                <el-form-item label="邮箱">
                    <el-input
                        v-model="form.email"
                        placeholder="请输入邮箱"
                    ></el-input>
                </el-form-item>
                <el-form-item label="密码">
                    <el-input
                        v-model="form.password"
                        show-password
                        placeholder="请输入密码"
                        @keyup.enter="handleLogin"
                    ></el-input>
                </el-form-item>
                <el-form-item>
                    <el-button
                        type="primary"
                        style="width: 100%"
                        @click="handleLogin"
                        >登录</el-button
                    >
                </el-form-item>
            </el-form>
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import request from "@/api/request";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

const router = useRouter();
const form = ref({ email: "", password: "" });

const handleLogin = async () => {
    if (!form.value.email || !form.value.password) {
        ElMessage.warning("请输入邮箱和密码");
        return;
    }
    try {
        const res = await request.post(
            "/login/access-token",
            new URLSearchParams({
                username: form.value.email,
                password: form.value.password,
            }),
            {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            }
        );
        localStorage.setItem("token", res.access_token);
        ElMessage.success("登录成功");
        router.push("/");
    } catch (err) {
        ElMessage.error("账号或密码错误");
    }
};
</script>

<style scoped>
.login-page {
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--el-bg-color-page);
}
.login-card {
    width: 400px;
    padding: 20px 10px;
}
.title {
    text-align: center;
    margin-bottom: 24px;
    color: var(--el-text-color-primary);
}
</style>
