<template>
  <el-card style="width:400px;margin:100px auto;">
    <el-form ref="formRef" :model="form">
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email"></el-input>
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" type="password"></el-input>
      </el-form-item>
      <el-button type="primary" @click="handleLogin">登录</el-button>
    </el-form>
  </el-card>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import request from '@/api/request'
import { useRouter } from 'vue-router'
const router = useRouter()
const form = ref({ email: '', password: '' })

const handleLogin = async () => {
  const res = await request.post('/login/access-token', new URLSearchParams({
    username: form.value.email,
    password: form.value.password
  }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
  localStorage.setItem('token', res.access_token)
  router.push('/')
}
</script>
